@preconcurrency import AVFoundation
import Foundation
import whisper

struct EduMindOnDeviceWhisperSegment {
    let text: String
    let start: Double
    let duration: Double
    let confidence: Double
}

struct EduMindOnDeviceWhisperResult {
    let text: String
    let segments: [EduMindOnDeviceWhisperSegment]
    let localeIdentifier: String
    let effectiveModel: String
}

private enum EduMindOnDeviceWhisperError: LocalizedError {
    case modelUnavailable(String)
    case downloadFailed(String)
    case initializationFailed(String)
    case audioDecodeFailed
    case transcriptionFailed(String)
    case emptyTranscript

    var errorDescription: String? {
        switch self {
        case .modelUnavailable(let message):
            return message
        case .downloadFailed(let message):
            return message
        case .initializationFailed(let message):
            return message
        case .audioDecodeFailed:
            return "当前音频无法转换为 Whisper 所需的本地离线格式"
        case .transcriptionFailed(let message):
            return message
        case .emptyTranscript:
            return "本机 Whisper 已完成处理，但未生成可用文本"
        }
    }
}

final class EduMindOnDeviceWhisperSession {
    private let context: OpaquePointer
    let effectiveModel: String

    init(modelURL: URL, effectiveModel: String) throws {
        var contextParams = whisper_context_default_params()
        contextParams.use_gpu = false
        contextParams.flash_attn = false

        guard let context = whisper_init_from_file_with_params(modelURL.path, contextParams) else {
            throw EduMindOnDeviceWhisperError.initializationFailed(
                "本机 Whisper 模型加载失败，请确认设备可用存储与内存充足，或切换更轻量的模型后重试"
            )
        }

        self.context = context
        self.effectiveModel = effectiveModel
    }

    deinit {
        whisper_free(context)
    }

    static let supportedModels: Set<String> = [
        "tiny",
        "base",
        "small",
        "medium",
        "large-v3-turbo-q5_0"
    ]

    static func resolveModelName(requestedModel: String, localeIdentifier: String) -> String {
        let normalizedRequestedModel = requestedModel.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
        switch normalizedRequestedModel {
        case "tiny", "base", "small", "medium":
            return normalizedRequestedModel
        case "large", "large-v3", "large-v3-turbo", "large-v3-turbo-q5_0", "turbo":
            return "large-v3-turbo-q5_0"
        default:
            let normalizedLocale = localeIdentifier.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
            if normalizedLocale.hasPrefix("zh") || normalizedLocale.hasPrefix("yue") || normalizedLocale.hasPrefix("wuu") {
                return "large-v3-turbo-q5_0"
            }
            return "small"
        }
    }

    static func localModelURL(for modelName: String) throws -> URL {
        guard supportedModels.contains(modelName) else {
            throw EduMindOnDeviceWhisperError.modelUnavailable("当前不支持本机 Whisper 模型：\(modelName)")
        }

        let baseDirectory = try FileManager.default.url(
            for: .applicationSupportDirectory,
            in: .userDomainMask,
            appropriateFor: nil,
            create: true
        )
        let modelDirectory = baseDirectory
            .appendingPathComponent("EduMind", isDirectory: true)
            .appendingPathComponent("WhisperModels", isDirectory: true)
        try FileManager.default.createDirectory(at: modelDirectory, withIntermediateDirectories: true)
        return modelDirectory.appendingPathComponent("ggml-\(modelName).bin")
    }

    static func ensureModel(named modelName: String) async throws -> URL {
        let destinationURL = try localModelURL(for: modelName)
        if FileManager.default.fileExists(atPath: destinationURL.path),
           let fileSize = try? destinationURL.resourceValues(forKeys: [.fileSizeKey]).fileSize,
           fileSize > 0
        {
            return destinationURL
        }

        guard let downloadURL = URL(
            string: "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-\(modelName).bin"
        ) else {
            throw EduMindOnDeviceWhisperError.downloadFailed("本机 Whisper 模型地址无效：\(modelName)")
        }

        do {
            let (temporaryURL, response) = try await URLSession.shared.download(from: downloadURL)
            guard let httpResponse = response as? HTTPURLResponse, (200 ... 299).contains(httpResponse.statusCode) else {
                throw EduMindOnDeviceWhisperError.downloadFailed("本机 Whisper 模型下载失败：\(modelName)")
            }

            if FileManager.default.fileExists(atPath: destinationURL.path) {
                try FileManager.default.removeItem(at: destinationURL)
            }

            try FileManager.default.moveItem(at: temporaryURL, to: destinationURL)
            var resourceValues = URLResourceValues()
            resourceValues.isExcludedFromBackup = true
            var mutableURL = destinationURL
            try? mutableURL.setResourceValues(resourceValues)
            return destinationURL
        } catch {
            let offlineHint = "首次使用本机 Whisper 需要先联网下载一次模型，下载完成后即可脱离后端独立转录。"
            throw EduMindOnDeviceWhisperError.downloadFailed("\(offlineHint) 当前模型：\(modelName)。原因：\(error.localizedDescription)")
        }
    }

    func transcribeChunk(
        audioURL: URL,
        chunkStartSeconds: Double,
        localeIdentifier: String,
        requestedLanguage: String
    ) throws -> EduMindOnDeviceWhisperResult {
        let pcmf32 = try Self.loadPCMFloat32(from: audioURL)
        guard !pcmf32.isEmpty else {
            throw EduMindOnDeviceWhisperError.emptyTranscript
        }

        var params = whisper_full_default_params(WHISPER_SAMPLING_BEAM_SEARCH)
        params.n_threads = Int32(max(2, min(4, ProcessInfo.processInfo.processorCount)))
        params.translate = false
        params.no_context = true
        params.no_timestamps = false
        params.single_segment = false
        params.print_special = false
        params.print_progress = false
        params.print_realtime = false
        params.print_timestamps = false
        params.token_timestamps = true
        params.max_len = 0
        params.max_tokens = 0
        params.split_on_word = true
        params.suppress_blank = true
        params.suppress_non_speech_tokens = true
        params.temperature = 0
        params.temperature_inc = 0.2
        params.entropy_thold = 2.4
        params.logprob_thold = -1.0
        params.no_speech_thold = 0.6
        params.beam_search.beam_size = 5

        let effectiveLocale = Self.whisperLanguageCode(localeIdentifier: localeIdentifier, requestedLanguage: requestedLanguage)
        let initialPrompt = Self.initialPrompt(localeIdentifier: localeIdentifier, requestedLanguage: requestedLanguage)

        let statusCode: Int32 = (effectiveLocale ?? "auto").withCString { localePointer in
            initialPrompt.withCString { promptPointer in
                params.language = effectiveLocale == nil ? nil : localePointer
                params.detect_language = effectiveLocale == nil
                params.initial_prompt = initialPrompt.isEmpty ? nil : promptPointer
                return pcmf32.withUnsafeBufferPointer { buffer in
                    whisper_full(context, params, buffer.baseAddress, Int32(buffer.count))
                }
            }
        }

        guard statusCode == 0 else {
            throw EduMindOnDeviceWhisperError.transcriptionFailed(
                "本机 Whisper 推理失败，请尝试切换更轻量模型或缩短单次视频时长后重试"
            )
        }

        let segmentCount = whisper_full_n_segments(context)
        var mergedText = ""
        var segments: [EduMindOnDeviceWhisperSegment] = []

        for index in 0 ..< segmentCount {
            guard let textPointer = whisper_full_get_segment_text(context, index) else {
                continue
            }
            let text = String(cString: textPointer).trimmingCharacters(in: .whitespacesAndNewlines)
            if text.isEmpty {
                continue
            }

            let start = Double(whisper_full_get_segment_t0(context, index)) / 100.0 + chunkStartSeconds
            let end = Double(whisper_full_get_segment_t1(context, index)) / 100.0 + chunkStartSeconds
            let tokenCount = whisper_full_n_tokens(context, index)
            var confidenceSum: Float = 0
            if tokenCount > 0 {
                for tokenIndex in 0 ..< tokenCount {
                    confidenceSum += whisper_full_get_token_p(context, index, tokenIndex)
                }
            }
            let averageConfidence = tokenCount > 0 ? Double(confidenceSum / Float(tokenCount)) : 0

            if mergedText.isEmpty {
                mergedText = text
            } else if !mergedText.hasSuffix(text) {
                mergedText += "\n" + text
            }

            segments.append(
                EduMindOnDeviceWhisperSegment(
                    text: text,
                    start: start,
                    duration: max(end - start, 0),
                    confidence: averageConfidence
                )
            )
        }

        let finalText = mergedText.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !finalText.isEmpty else {
            throw EduMindOnDeviceWhisperError.emptyTranscript
        }

        return EduMindOnDeviceWhisperResult(
            text: finalText,
            segments: segments,
            localeIdentifier: effectiveLocale ?? localeIdentifier,
            effectiveModel: effectiveModel
        )
    }

    private static func whisperLanguageCode(localeIdentifier: String, requestedLanguage: String) -> String? {
        let normalizedRequestedLanguage = requestedLanguage.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
        if normalizedRequestedLanguage.isEmpty || normalizedRequestedLanguage == "auto" {
            let normalizedLocale = localeIdentifier.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
            if normalizedLocale.hasPrefix("zh") || normalizedLocale.hasPrefix("yue") || normalizedLocale.hasPrefix("wuu") {
                return "zh"
            }
            if normalizedLocale.hasPrefix("en") {
                return "en"
            }
            if normalizedLocale.hasPrefix("ja") {
                return "ja"
            }
            return nil
        }

        if normalizedRequestedLanguage.contains("english") || normalizedRequestedLanguage.hasPrefix("en") {
            return "en"
        }
        if normalizedRequestedLanguage.contains("japanese") || normalizedRequestedLanguage.hasPrefix("ja") {
            return "ja"
        }
        if normalizedRequestedLanguage.contains("zh")
            || normalizedRequestedLanguage.contains("chinese")
            || normalizedRequestedLanguage.contains("普通话")
            || normalizedRequestedLanguage.contains("中文")
            || normalizedRequestedLanguage.contains("粤")
            || normalizedRequestedLanguage.contains("吴")
        {
            return "zh"
        }

        return nil
    }

    private static func initialPrompt(localeIdentifier: String, requestedLanguage: String) -> String {
        let normalizedLocale = localeIdentifier.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
        let normalizedRequestedLanguage = requestedLanguage.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()

        if normalizedLocale.hasPrefix("zh")
            || normalizedLocale.hasPrefix("yue")
            || normalizedLocale.hasPrefix("wuu")
            || normalizedRequestedLanguage.contains("zh")
            || normalizedRequestedLanguage.contains("中文")
            || normalizedRequestedLanguage.contains("粤")
            || normalizedRequestedLanguage.contains("吴")
        {
            return "以下是教学视频的中文逐字转录，内容可能包含普通话、儿化音、粤语口语或吴语口语，请尽量保留原意，准确输出术语、数字和专有名词，并使用规范中文标点。"
        }

        if normalizedLocale.hasPrefix("en") || normalizedRequestedLanguage.contains("english") {
            return "The following is an educational video transcript. Preserve terminology, numbers, and proper nouns accurately."
        }

        return ""
    }

    private static func loadPCMFloat32(from audioURL: URL) throws -> [Float] {
        let inputFile = try AVAudioFile(forReading: audioURL)
        guard let outputFormat = AVAudioFormat(
            commonFormat: .pcmFormatFloat32,
            sampleRate: Double(WHISPER_SAMPLE_RATE),
            channels: 1,
            interleaved: false
        ) else {
            throw EduMindOnDeviceWhisperError.audioDecodeFailed
        }
        guard let converter = AVAudioConverter(from: inputFile.processingFormat, to: outputFormat) else {
            throw EduMindOnDeviceWhisperError.audioDecodeFailed
        }

        converter.sampleRateConverterQuality = AVAudioQuality.max.rawValue

        let inputFrameCapacity: AVAudioFrameCount = 8_192
        let ratio = outputFormat.sampleRate / max(inputFile.processingFormat.sampleRate, 1)
        let outputFrameCapacity = AVAudioFrameCount(max(4_096, Int(Double(inputFrameCapacity) * ratio) + 1_024))
        var pcmf32: [Float] = []

        while true {
            guard let inputBuffer = AVAudioPCMBuffer(
                pcmFormat: inputFile.processingFormat,
                frameCapacity: inputFrameCapacity
            ) else {
                throw EduMindOnDeviceWhisperError.audioDecodeFailed
            }
            try inputFile.read(into: inputBuffer)
            if inputBuffer.frameLength == 0 {
                break
            }

            guard let outputBuffer = AVAudioPCMBuffer(
                pcmFormat: outputFormat,
                frameCapacity: outputFrameCapacity
            ) else {
                throw EduMindOnDeviceWhisperError.audioDecodeFailed
            }

            var conversionError: NSError?
            let status = converter.convert(to: outputBuffer, error: &conversionError) { _, outputStatus in
                outputStatus.pointee = .haveData
                return inputBuffer
            }

            if let conversionError {
                throw conversionError
            }
            if status == .error {
                throw EduMindOnDeviceWhisperError.audioDecodeFailed
            }

            let frameLength = Int(outputBuffer.frameLength)
            if frameLength > 0, let channelData = outputBuffer.floatChannelData?.pointee {
                pcmf32.append(contentsOf: UnsafeBufferPointer(start: channelData, count: frameLength))
            }
        }

        return pcmf32
    }
}
