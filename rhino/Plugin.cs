using System.Net;
using System.Net.Sockets;
using System.Runtime.InteropServices;
using System.Text.Json;
using Rhino;
using Rhino.Commands;
using Rhino.DocObjects;
using Rhino.Geometry;
using Rhino.PlugIns;

namespace NakedEye3D;

[Guid("96750993-419a-4c83-9404-e287e4ef6450")]
public sealed class Plugin : PlugIn
{
    protected override void OnShutdown() => Session.Stop();
}

// Local coordinates: x right, y up, z toward viewer. Units are fractions
// of the original camera-to-target distance; this prototype is uncalibrated.
public sealed record Sample(double X, double Y, double Z, bool Grip, double HandX, double HandY);

internal static class Session
{
    static UdpClient? socket;
    static Rhino.Display.RhinoView? view;
    static ViewportInfo? original;
    static ViewportInfo? basis;
    static DateTime last = DateTime.UtcNow;
    static bool gripping;
    static double neutralX, neutralY;
    static double distance;

    internal static bool Start(RhinoDoc doc)
    {
        if (socket != null) return false;
        var candidate = doc.Views.ActiveView;
        if (candidate == null || !candidate.ActiveViewport.IsPerspectiveProjection) return false;
        var receiver = new UdpClient(new IPEndPoint(IPAddress.Loopback, 39539));
        socket = receiver;
        view = candidate;
        original = new ViewportInfo(candidate.ActiveViewport);
        basis = new ViewportInfo(candidate.ActiveViewport);
        distance = candidate.ActiveViewport.CameraLocation.DistanceTo(candidate.ActiveViewport.CameraTarget);
        last = DateTime.UtcNow;
        RhinoApp.Idle += Tick;
        return true;
    }

    internal static void Stop()
    {
        RhinoApp.Idle -= Tick;
        socket?.Dispose(); socket = null;
        if (view != null && original != null)
        {
            view.ActiveViewport.SetViewProjection(original, false);
            view.Redraw();
        }
        original?.Dispose(); basis?.Dispose();
        original = basis = null; view = null; gripping = false;
    }

    static void Tick(object? sender, EventArgs e)
    {
        try
        {
            if (socket == null || view == null || basis == null) return;
            Sample? sample = null;
            // Bound per-frame work; discard queued packets in favor of the newest.
            for (int i = 0; i < 64 && socket.Available > 0; i++)
            {
                IPEndPoint endpoint = new(IPAddress.Loopback, 0);
                var bytes = socket.Receive(ref endpoint);
                if (bytes.Length > 2048) continue;
                try { sample = JsonSerializer.Deserialize<Sample>(bytes); }
                catch (JsonException) { }
            }
            var now = DateTime.UtcNow;
            if (sample == null)
            {
                if ((now - last).TotalSeconds > .25) gripping = false;
                return;
            }
            if (!new[] { sample.X, sample.Y, sample.Z, sample.HandX, sample.HandY }.All(double.IsFinite)) return;
            double dt = Math.Clamp((now - last).TotalSeconds, 0, .05);
            last = now;
            if (sample.Grip)
            {
                if (!gripping) { neutralX = sample.HandX; neutralY = sample.HandY; }
                gripping = true;
                var target = basis.TargetPoint;
                double Rate(double value) => Math.Abs(value) < .04 ? 0 : Math.Clamp(value, -.5, .5);
                var yaw = Transform.Rotation(-Rate(sample.HandX - neutralX) * dt, basis.CameraY, target);
                var pitch = Transform.Rotation(Rate(sample.HandY - neutralY) * dt, basis.CameraX, target);
                var rotation = yaw * pitch;
                var location = basis.CameraLocation; location.Transform(rotation);
                var direction = basis.CameraDirection; direction.Transform(rotation);
                var up = basis.CameraUp; up.Transform(rotation);
                basis.SetCameraLocation(location); basis.SetCameraDirection(direction); basis.SetCameraUp(up);
                view.ActiveViewport.SetViewProjection(basis, false);
            }
            else
            {
                gripping = false;
                using var projection = new ViewportInfo(basis);
                projection.UnlockFrustumSymmetry();
                basis.GetFrustum(out double left, out double right, out double bottom, out double top, out double near, out double far);
                double x = Math.Clamp(sample.X, -.3, .3) * distance;
                double y = Math.Clamp(sample.Y, -.3, .3) * distance;
                double z = Math.Clamp(sample.Z, -.3, .3) * distance;
                projection.SetCameraLocation(basis.CameraLocation + basis.CameraX * x + basis.CameraY * y + basis.CameraZ * z);
                double ratio = distance / (distance + z);
                if (!projection.SetFrustum((left - x * near / distance) * ratio, (right - x * near / distance) * ratio,
                    (bottom - y * near / distance) * ratio, (top - y * near / distance) * ratio, near, far))
                    throw new InvalidOperationException("SetFrustum failed");
                if (!view.ActiveViewport.SetViewProjection(projection, false)) throw new InvalidOperationException("Projection failed");
            }
            view.Redraw();
        }
        catch (Exception ex) { RhinoApp.WriteLine("NakedEye3D stopped: " + ex.Message); Stop(); }
    }
}

[Guid("96a0a135-dd52-428c-a40e-325af9ea8ed0")]
public sealed class StartCommand : Command
{
    public override string EnglishName => "NakedEye3DStart";
    protected override Result RunCommand(RhinoDoc doc, RunMode mode)
    {
        try { return Session.Start(doc) ? Result.Success : Result.Failure; }
        catch (Exception ex) { RhinoApp.WriteLine(ex.Message); return Result.Failure; }
    }
}

[Guid("b9f3501a-e4c7-4e20-8f64-7383eb915fdd")]
public sealed class StopCommand : Command
{
    public override string EnglishName => "NakedEye3DStop";
    protected override Result RunCommand(RhinoDoc doc, RunMode mode) { Session.Stop(); return Result.Success; }
}
