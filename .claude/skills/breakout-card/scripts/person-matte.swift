// Person matte for the breakout card.
// Reads a video, runs Apple Vision person segmentation (accurate, stateful across frames)
// and writes raw 8-bit gray frames (W x H) to stdout for ffmpeg. build_plates.py compiles and runs it.
// usage: person-matte <in.mp4> <W> <H> | ffmpeg -f rawvideo -pix_fmt gray -s WxH -r 30 -i - ...
import AVFoundation
import Vision
import CoreImage
import Foundation

let args = CommandLine.arguments
let url = URL(fileURLWithPath: args[1])
let W = Int(args[2])!, H = Int(args[3])!

let asset = AVURLAsset(url: url)
let track = asset.tracks(withMediaType: .video)[0]
let reader = try! AVAssetReader(asset: asset)
let out = AVAssetReaderTrackOutput(track: track, outputSettings: [kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32BGRA])
out.alwaysCopiesSampleData = false
reader.add(out)
reader.startReading()

let request = VNGeneratePersonSegmentationRequest()
request.qualityLevel = .accurate
request.outputPixelFormat = kCVPixelFormatType_OneComponent8
let seq = VNSequenceRequestHandler()
let ctx = CIContext(options: [.workingColorSpace: NSNull(), .outputColorSpace: NSNull()])
var buf = [UInt8](repeating: 0, count: W * H)
let stdout = FileHandle.standardOutput
var n = 0

while let sample = out.copyNextSampleBuffer() {
    guard let pb = CMSampleBufferGetImageBuffer(sample) else { continue }
    try! seq.perform([request], on: pb)
    guard let mask = request.results?.first?.pixelBuffer else { continue }
    let mi = CIImage(cvPixelBuffer: mask)
    let sx = CGFloat(W) / mi.extent.width, sy = CGFloat(H) / mi.extent.height
    let scaled = mi.transformed(by: CGAffineTransform(scaleX: sx, y: sy))
    buf.withUnsafeMutableBytes { p in
        ctx.render(scaled, toBitmap: p.baseAddress!, rowBytes: W, bounds: CGRect(x: 0, y: 0, width: W, height: H), format: .L8, colorSpace: nil)
    }
    stdout.write(Data(buf))
    n += 1
    if n % 100 == 0 { FileHandle.standardError.write("frames \(n)\n".data(using: .utf8)!) }
}
FileHandle.standardError.write("done \(n) frames, mask \(W)x\(H)\n".data(using: .utf8)!)
