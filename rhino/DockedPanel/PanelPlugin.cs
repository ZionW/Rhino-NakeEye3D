using System.Runtime.InteropServices;
using Eto.Forms;
using Rhino;
using Rhino.Commands;
using Rhino.PlugIns;
using Rhino.UI;

[assembly: Guid("49e67db1-636e-4d38-aeae-52724c1b8ad5")]

namespace RhinoNakeEye3D.PanelHost;

[Guid("49e67db1-636e-4d38-aeae-52724c1b8ad5")]
public sealed class PanelPlugin : PlugIn
{
    protected override LoadReturnCode OnLoad(ref string errorMessage)
    {
        Panels.RegisterPanel(this, typeof(TrackingHost), "Rhino NakeEye3D", typeof(PanelPlugin).Assembly, "RhinoNakeEye3D.DockPanel.PanelIcon.svg", PanelType.PerDoc);
        return LoadReturnCode.Success;
    }
}

[Guid("eabb6fb8-4314-4429-8810-bb8dc24b8923")]
public sealed class TrackingHost : Panel
{
    public static TrackingHost? Pending { get; private set; }
    public Action? StopTracking { get; set; }
    public TrackingHost()
    {
        Content = new Label { Text = "正在載入追蹤控制…" };
        RhinoApp.Idle += Initialize;
        Load += (_, _) => { if (Content is Label) { RhinoApp.Idle -= Initialize; RhinoApp.Idle += Initialize; } };
        UnLoad += (_, _) => { RhinoApp.Idle -= Initialize; StopTracking?.Invoke(); };
    }
    private void Initialize(object? sender, EventArgs e)
    {
        if (RhinoApp.InCommand != 0) return;
        RhinoApp.Idle -= Initialize;
        var root = Environment.GetEnvironmentVariable("NAKEDEYE3D_ROOT");
        if (string.IsNullOrEmpty(root))
        {
            var folder = new DirectoryInfo(Path.GetDirectoryName(typeof(TrackingHost).Assembly.Location)!);
            while (folder != null && !File.Exists(Path.Combine(folder.FullName, "tools", "webcam_tracker.py"))) folder = folder.Parent;
            root = folder?.FullName;
            if (root != null) Environment.SetEnvironmentVariable("NAKEDEYE3D_ROOT", root);
        }
        if (string.IsNullOrEmpty(root))
        {
            Content = new Label { Text = "請先執行 rhino/OpenDockedPanel.py" };
            return;
        }
        Pending = this;
        try { RhinoApp.RunScript($"_-ScriptEditor _Run \"{Path.Combine(root, "rhino", "TrackingPanel.py")}\"", false); }
        finally { Pending = null; }
    }
}

public sealed class OpenTrackingPanel : Rhino.Commands.Command
{
    public override string EnglishName => "NakeEye3DDockPanel";
    protected override Result RunCommand(RhinoDoc doc, RunMode mode)
    {
        Panels.OpenPanel(typeof(TrackingHost).GUID);
        return Result.Success;
    }
}
