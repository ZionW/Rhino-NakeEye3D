import Cocoa
import AVFoundation
import Foundation

let app = NSApplication.shared
app.setActivationPolicy(.accessory)
var answered = false
var allowed = false
AVCaptureDevice.requestAccess(for: .video) { granted in
    allowed = granted
    answered = true
}
while !answered {
    RunLoop.current.run(until: Date(timeIntervalSinceNow: 0.1))
}
let root = Bundle.main.bundleURL.deletingLastPathComponent().deletingLastPathComponent()
let clientArgs = Array(CommandLine.arguments.dropFirst())
let client = clientArgs.contains("touchdesigner") ? "touchdesigner" : (clientArgs.contains("blender") ? "blender" : "rhino")
let runtime = root.appendingPathComponent(client == "rhino" ? "runtime" : "runtime/" + client)
try? FileManager.default.createDirectory(at: runtime, withIntermediateDirectories: true)
if !allowed {
    let status: [String: Any] = ["message": "相機權限未允許：請在系統設定 → 隱私權與安全性 → 相機，允許裸視3D Webcam", "time": Date().timeIntervalSince1970, "error": true]
    if let data = try? JSONSerialization.data(withJSONObject: status) {
        try? data.write(to: runtime.appendingPathComponent("status.json"), options: .atomic)
    }
    exit(1)
}
let worker = Process()
worker.executableURL = root.appendingPathComponent(".venv/bin/python")
worker.arguments = [root.appendingPathComponent("tools/webcam_tracker.py").path] + clientArgs
worker.currentDirectoryURL = root
let log = runtime.appendingPathComponent("webcam.log")
FileManager.default.createFile(atPath: log.path, contents: nil)
let handle = try FileHandle(forWritingTo: log)
worker.standardOutput = handle
worker.standardError = handle
try worker.run()
worker.waitUntilExit()
exit(worker.terminationStatus)
