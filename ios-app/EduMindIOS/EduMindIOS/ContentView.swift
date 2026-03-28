//
//  ContentView.swift
//  EduMindIOS
//
//  Created by yuan on 2026/3/12.
//

@preconcurrency import AVFoundation
import Foundation
import OSLog
import Speech
import SwiftUI
import UniformTypeIdentifiers
import UIKit
import WebKit

private enum EduMindLogLevel {
    case debug
    case info
    case notice
    case error
    case fault
}

private enum EduMindLog {
    private static let logger = Logger(
        subsystem: Bundle.main.bundleIdentifier ?? "EduMindIOS",
        category: "EduMindWeb"
    )

    private static func prefix(for level: EduMindLogLevel) -> String {
        switch level {
        case .debug:
            return "[DEBUG]"
        case .info:
            return "[INFO]"
        case .notice:
            return "[NOTICE]"
        case .error:
            return "[ERROR]"
        case .fault:
            return "[FAULT]"
        }
    }

    private static func line(for level: EduMindLogLevel, scope: String?, message: String) -> String {
        if message.hasPrefix("[") {
            return message
        }
        let scopeText = scope.map { "[\($0)]" } ?? ""
        return "\(prefix(for: level))\(scopeText) \(message)"
    }

    static func write(_ level: EduMindLogLevel, scope: String? = nil, _ message: String) {
        let line = line(for: level, scope: scope, message: message)
        switch level {
        case .debug:
            logger.debug("\(line, privacy: .public)")
        case .info:
            logger.info("\(line, privacy: .public)")
        case .notice:
            logger.notice("\(line, privacy: .public)")
        case .error:
            logger.error("\(line, privacy: .public)")
        case .fault:
            logger.fault("\(line, privacy: .public)")
        }
        #if DEBUG
        print(line)
        #endif
    }

    static func debug(_ scope: String, _ message: String) {
        write(.debug, scope: scope, message)
    }

    static func info(_ scope: String, _ message: String) {
        write(.info, scope: scope, message)
    }

    static func notice(_ scope: String, _ message: String) {
        write(.notice, scope: scope, message)
    }

    static func error(_ scope: String, _ message: String) {
        write(.error, scope: scope, message)
    }

    static func fault(_ scope: String, _ message: String) {
        write(.fault, scope: scope, message)
    }
}

private enum WebAssets {
    static let indexName = "index"
    static let indexExtension = "html"
    static let preferredSubdirectory = "WebAssets"

    static func indexURL() -> URL? {
        // Prefer WebAssets folder, then fall back to app bundle root.
        if let bundled = Bundle.main.url(
            forResource: indexName,
            withExtension: indexExtension,
            subdirectory: preferredSubdirectory
        ) {
            return bundled
        }
        return Bundle.main.url(forResource: indexName, withExtension: indexExtension)
    }
}

private struct H5WebView: UIViewRepresentable {
    private enum WebViewErrorCode: String {
        case webAssetMissing = "ERR_WEB_ASSET_MISSING"
        case legacyAssetPath = "ERR_LEGACY_ASSET_PATH"
        case webBuildLayout = "ERR_WEB_BUILD_LAYOUT"
        case navigationFail = "ERR_NAVIGATION_FAIL"
        case navigationInitFail = "ERR_NAVIGATION_INIT_FAIL"
        case navigationTimeout = "ERR_NAVIGATION_TIMEOUT"
    }

    private static let nativeConfigScript = """
        (function() {
          window.__edumindNativeConfig = Object.assign({}, window.__edumindNativeConfig || {}, \(nativeConfigJSONString()));
        })();
    """

    func makeCoordinator() -> Coordinator {
        Coordinator()
    }

    func makeUIView(context: Context) -> WKWebView {
        let configuration = WKWebViewConfiguration()
        configuration.defaultWebpagePreferences.allowsContentJavaScript = true
        configuration.allowsInlineMediaPlayback = true
        configuration.allowsAirPlayForMediaPlayback = true
        configuration.allowsPictureInPictureMediaPlayback = true
        configuration.mediaTypesRequiringUserActionForPlayback = []
        configuration.setURLSchemeHandler(context.coordinator, forURLScheme: Coordinator.offlineVideoScheme)
        configuration.userContentController.add(context.coordinator, name: Coordinator.logHandlerName)
        configuration.userContentController.add(context.coordinator, name: Coordinator.nativeBridgeHandlerName)
        configuration.userContentController.add(context.coordinator, name: Coordinator.pageStateHandlerName)
        configuration.userContentController.addUserScript(WKUserScript(
            source: Self.nativeConfigScript,
            injectionTime: .atDocumentStart,
            forMainFrameOnly: true
        ))
        configuration.userContentController.addUserScript(WKUserScript(
            source: Coordinator.nativeBridgeScript,
            injectionTime: .atDocumentStart,
            forMainFrameOnly: true
        ))
        configuration.userContentController.addUserScript(WKUserScript(
            source: Coordinator.consoleBridgeScript,
            injectionTime: .atDocumentStart,
            forMainFrameOnly: false
        ))
        configuration.userContentController.addUserScript(WKUserScript(
            source: Coordinator.pageStateBridgeScript,
            injectionTime: .atDocumentStart,
            forMainFrameOnly: false
        ))
        configuration.userContentController.addUserScript(WKUserScript(
            source: Coordinator.mountWatchdogScript,
            injectionTime: .atDocumentEnd,
            forMainFrameOnly: true
        ))

        let webView = WKWebView(frame: .zero, configuration: configuration)
        webView.scrollView.contentInsetAdjustmentBehavior = .never
        webView.scrollView.bounces = false
        webView.backgroundColor = .systemBackground
        webView.isOpaque = false
        webView.navigationDelegate = context.coordinator
        context.coordinator.attach(webView: webView)
        if #available(iOS 16.4, *) {
            webView.isInspectable = true
        }
        context.coordinator.startLoadTimeout(for: webView)
        loadContent(into: webView)
        return webView
    }

    func updateUIView(_ uiView: WKWebView, context: Context) {}

    static func dismantleUIView(_ uiView: WKWebView, coordinator: Coordinator) {
        uiView.navigationDelegate = nil
        uiView.configuration.userContentController.removeScriptMessageHandler(forName: Coordinator.logHandlerName)
        uiView.configuration.userContentController.removeScriptMessageHandler(forName: Coordinator.nativeBridgeHandlerName)
        uiView.configuration.userContentController.removeScriptMessageHandler(forName: Coordinator.pageStateHandlerName)
    }

    private func loadContent(into webView: WKWebView) {
        guard let indexURL = WebAssets.indexURL() else {
            EduMindLog.error("WebView", "index.html not found in bundle. resourceURL=\(Bundle.main.resourceURL?.path ?? "<nil>")")
            Self.renderErrorPage(
                in: webView,
                code: .webAssetMissing,
                title: "未找到前端资源",
                details: "Bundle 内未找到 WebAssets/index.html。",
                recovery: "请执行：bash ios-app/sync_ios_web_assets.sh，并确认 iOS 包内已包含 WebAssets/index.html。"
            )
            return
        }

        let allowedPath = indexURL.deletingLastPathComponent()
        EduMindLog.info("WebView", "loading index from \(indexURL.path)")
        EduMindLog.info("WebView", "allowing read access to \(allowedPath.path)")
        EduMindLog.debug("WebView", "bundle resourceURL=\(Bundle.main.resourceURL?.path ?? "<nil>")")
        let missingAssets = missingRequiredAssets(near: indexURL)
        if !missingAssets.isEmpty {
            let missingText = missingAssets.joined(separator: ", ")
            EduMindLog.error("WebView", "missing required web assets: \(missingText)")
            Self.renderErrorPage(
                in: webView,
                code: .webAssetMissing,
                title: "前端资源不完整",
                details: "缺少关键文件：\(missingText)",
                recovery: "请执行：bash ios-app/sync_ios_web_assets.sh，并确认 iOS 包内包含 index.html、index.js、index.css。"
            )
            return
        }
        do {
            let html = try String(contentsOf: indexURL, encoding: .utf8)
            EduMindLog.debug("WebView", "index.html chars=\(html.count)")
            if usesLegacyAbsoluteAssetPaths(in: html) {
                EduMindLog.error("WebView", "detected legacy absolute asset paths in \(indexURL.path)")
                Self.renderErrorPage(
                    in: webView,
                    code: .legacyAssetPath,
                    title: "前端资源路径不兼容",
                    details: "检测到 index.html 使用了绝对资源路径，WKWebView 本地资源模式无法正确加载。",
                    recovery: "请执行：bash ios-app/sync_ios_web_assets.sh，确认当前使用的是 iOS 打包资源而不是旧网页构建产物。"
                )
                return
            }
            if usesWebBuildAssetLayout(in: html) {
                EduMindLog.error("WebView", "detected web build asset layout in \(indexURL.path)")
                Self.renderErrorPage(
                    in: webView,
                    code: .webBuildLayout,
                    title: "检测到错误的前端构建产物",
                    details: "当前 iOS 容器需要 index.js / index.css 稳定布局，但 index.html 仍指向 ./assets/* 路径。",
                    recovery: "请执行：bash ios-app/sync_ios_web_assets.sh，确认 mobile-frontend 使用的是 iOS 构建模式。"
                )
                return
            }
        } catch {
            EduMindLog.notice("WebView", "failed to inspect index.html before load: \(error.localizedDescription)")
        }

        webView.loadFileURL(indexURL, allowingReadAccessTo: allowedPath)
        EduMindLog.info("WebView", "loadFileURL requested")
    }

    private static func nativeConfigJSONString() -> String {
        let configuredAPIBase = (
            Bundle.main.object(forInfoDictionaryKey: "EDUMIND_API_BASE_URL") as? String
        )?
            .trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
        let apiBase = configuredAPIBase.isEmpty ? "http://yuandeMacBook-Pro.local:2004" : configuredAPIBase
        EduMindLog.info(
            "WebView",
            "native api base=\(apiBase) | source=\(configuredAPIBase.isEmpty ? "fallback-local-hostname" : "info-plist")"
        )

        let payload: [String: String] = [
            "apiBaseUrl": apiBase
        ]

        guard
            let data = try? JSONSerialization.data(withJSONObject: payload, options: []),
            let text = String(data: data, encoding: .utf8)
        else {
            return #"{"apiBaseUrl":""}"#
        }
        return text
    }

    private func usesLegacyAbsoluteAssetPaths(in html: String) -> Bool {
        html.contains("src=\"/") || html.contains("href=\"/") || html.contains("src='/") || html.contains("href='/")
    }

    private func usesWebBuildAssetLayout(in html: String) -> Bool {
        html.contains("src=\"./assets/") ||
            html.contains("src='./assets/") ||
            html.contains("href=\"./assets/") ||
            html.contains("href='./assets/")
    }

    private func missingRequiredAssets(near indexURL: URL) -> [String] {
        let baseURL = indexURL.deletingLastPathComponent()
        let requiredFiles = ["index.html", "index.js", "index.css"]
        return requiredFiles.filter { requiredFile in
            !FileManager.default.fileExists(atPath: baseURL.appendingPathComponent(requiredFile).path)
        }
    }

    private static func renderErrorPage(
        in webView: WKWebView,
        code: WebViewErrorCode,
        title: String,
        details: String,
        recovery: String
    ) {
        EduMindLog.error("WebView", "render error page code=\(code.rawValue) title=\(title) details=\(details)")
        webView.loadHTMLString(
            errorPageHTML(code: code.rawValue, title: title, details: details, recovery: recovery),
            baseURL: nil
        )
    }

    private static func errorPageHTML(code: String, title: String, details: String, recovery: String) -> String {
        """
        <div style="font-family:-apple-system,BlinkMacSystemFont,sans-serif;padding:20px;color:#111827;background:#f8fafc;min-height:100vh;box-sizing:border-box;">
          <div style="max-width:720px;margin:0 auto;background:#ffffff;border:1px solid #e5e7eb;border-radius:18px;padding:20px;box-shadow:0 12px 30px rgba(15,23,42,0.08);">
            <div style="display:inline-block;margin-bottom:12px;padding:4px 10px;border-radius:999px;background:#fee2e2;color:#b91c1c;font-size:12px;font-weight:600;">\(escapeHTML(code))</div>
            <h2 style="margin:0 0 10px;font-size:22px;line-height:1.35;">\(escapeHTML(title))</h2>
            <p style="margin:0 0 14px;color:#475569;line-height:1.7;">\(escapeHTML(details))</p>
            <div style="margin:0 0 14px;padding:12px 14px;border-radius:12px;background:#f8fafc;border:1px solid #e2e8f0;color:#0f172a;line-height:1.7;">
              <strong>建议处理：</strong><br />\(escapeHTML(recovery))
            </div>
            <div style="font-size:13px;color:#64748b;line-height:1.6;">请同时查看 Xcode 控制台中的 <code>[EduMindWeb]</code> 日志、probe 日志和 mount watchdog 输出。</div>
          </div>
        </div>
        """
    }

    private static func escapeHTML(_ value: String) -> String {
        value
            .replacingOccurrences(of: "&", with: "&amp;")
            .replacingOccurrences(of: "<", with: "&lt;")
            .replacingOccurrences(of: ">", with: "&gt;")
            .replacingOccurrences(of: "\"", with: "&quot;")
            .replacingOccurrences(of: "\n", with: "<br />")
    }

    final class Coordinator: NSObject, WKNavigationDelegate, WKScriptMessageHandler, WKURLSchemeHandler {
        private struct NativeSelectedVideo {
            let taskId: String
            let workingURL: URL
            let fileName: String
            let fileSize: Int
            let fileExt: String
        }

        private struct NativeTranscriptionResult {
            let text: String
            let segments: [[String: Any]]
            let localeIdentifier: String
            let engine: String
        }

        private struct NativeAudioChunk {
            let index: Int
            let total: Int
            let startSeconds: Double
            let durationSeconds: Double
            let url: URL
            let requiresCleanup: Bool
        }

        private enum NativeOfflineTranscriptionError: LocalizedError {
            case presenterUnavailable
            case pickerBusy
            case transcriptionBusy
            case pickerCancelled
            case invalidSelection
            case audioExtractionUnavailable
            case speechAuthorizationDenied
            case recognizerUnavailable
            case onDeviceRecognitionUnavailable
            case onDeviceWhisperUnavailable
            case backendWhisperUnavailable
            case emptyTranscript

            var errorDescription: String? {
                switch self {
                case .presenterUnavailable:
                    return "当前 iOS 容器无法打开本地视频选择器"
                case .pickerBusy:
                    return "已有一个原生离线转录任务正在选择视频，请稍后再试"
                case .transcriptionBusy:
                    return "已有一个原生离线转录任务正在执行，请等待完成后再试"
                case .pickerCancelled:
                    return "已取消本地视频选择"
                case .invalidSelection:
                    return "未能读取所选视频文件"
                case .audioExtractionUnavailable:
                    return "当前视频无法提取音频，无法进行本地转录"
                case .speechAuthorizationDenied:
                    return "未获得语音识别权限，无法进行本地离线转录"
                case .recognizerUnavailable:
                    return "当前设备不支持所选语言的语音识别"
                case .onDeviceRecognitionUnavailable:
                    return "当前设备或当前语言暂不支持 Apple 端侧离线识别"
                case .onDeviceWhisperUnavailable:
                    return "当前设备上的本机 Whisper 离线模型暂不可用"
                case .backendWhisperUnavailable:
                    return "Apple 端侧识别不可用，且未能连接后端 Whisper fallback"
                case .emptyTranscript:
                    return "本地识别已完成，但未生成可用文本"
                }
            }
        }

        private let offlineChunkDurationSeconds: Double = 15
        private let offlineChunkOverlapSeconds: Double = 1.5
        private let offlineMinimumChunkSeconds: Double = 1

        static let logHandlerName = "edumindLog"
        static let nativeBridgeHandlerName = "edumindNative"
        static let pageStateHandlerName = "edumindPageState"
        static let offlineVideoScheme = "edumind-local"
        private static let offlineVideoHost = "offline-video"
        private static let offlineVideoManifestKey = "edumind.offline-video-manifest"

        static let nativeBridgeScript = """
            (function() {
              if (window.__edumindNativeBridge) return;

              var handlerName = 'edumindNative';
              var version = '1';
              var eventPrefix = 'edumind-native:';
              var seq = 0;
              var pending = Object.create(null);

              function dispatchEvent(name, detail) {
                window.dispatchEvent(new CustomEvent(eventPrefix + name, {
                  detail: detail || {}
                }));
              }

              function send(action, payload) {
                return new Promise(function(resolve, reject) {
                  var requestId = 'native-' + Date.now() + '-' + (++seq);
                  pending[requestId] = { resolve: resolve, reject: reject };
                  try {
                    window.webkit.messageHandlers[handlerName].postMessage({
                      requestId: requestId,
                      action: String(action || ''),
                      payload: payload || {}
                    });
                  } catch (error) {
                    delete pending[requestId];
                    reject(error);
                  }
                });
              }

              window.__edumindHandleNativeResponse = function(message) {
                var body = message || {};
                var requestId = String(body.requestId || '');
                var entry = pending[requestId];
                if (!entry) return false;
                delete pending[requestId];
                if (body.success === false) {
                  entry.reject(new Error(String(body.error || 'Native bridge request failed')));
                  return true;
                }
                entry.resolve(body.payload || {});
                return true;
              };

              window.__edumindReceiveNativeEvent = function(name, payload) {
                dispatchEvent(String(name || 'event'), payload || {});
                return true;
              };

              window.__edumindNativeBridge = {
                version: version,
                isAvailable: function() {
                  return true;
                },
                send: send,
                on: function(name, listener) {
                  var eventName = eventPrefix + String(name || '');
                  window.addEventListener(eventName, listener);
                  return function() {
                    window.removeEventListener(eventName, listener);
                  };
                }
              };

              dispatchEvent('bridge-ready', {
                handlerName: handlerName,
                version: version
              });
            })();
        """

        static let pageStateBridgeScript = """
            (function() {
              if (window.__edumindPageStateBridge) return;

              function normalizePayload(payload) {
                if (payload && typeof payload === 'object' && !Array.isArray(payload)) {
                  return payload;
                }
                return {
                  rawValue: payload == null ? '' : String(payload)
                };
              }

              function report(payload) {
                try {
                  window.webkit.messageHandlers.edumindPageState.postMessage(normalizePayload(payload));
                  return true;
                } catch (error) {
                  return false;
                }
              }

              window.__edumindPageStateBridge = {
                report: report
              };

              window.__edumindReportPageState = report;
            })();
        """

        static let consoleBridgeScript = """
            (function() {
              if (window.__edumindConsoleHooked__) return;
              window.__edumindConsoleHooked__ = true;
              function post(level, payload) {
                try {
                  window.webkit.messageHandlers.edumindLog.postMessage({
                    level: level,
                    payload: String(payload || '')
                  });
                } catch (e) {}
              }
              function wrapConsole(level) {
                var raw = console[level];
                console[level] = function() {
                  try {
                    var text = Array.prototype.slice.call(arguments).map(function(v) {
                      return typeof v === 'string' ? v : JSON.stringify(v);
                    }).join(' ');
                    post('console.' + level, text);
                  } catch (e) {}
                  return raw && raw.apply(console, arguments);
                };
              }
              ['log', 'info', 'warn', 'error', 'debug'].forEach(wrapConsole);
              window.__edumindNativeProbe = function(stage) {
                try {
                  var app = document.getElementById('app');
                  var payload = {
                    stage: stage || 'probe',
                    href: String(window.location.href || ''),
                    readyState: String(document.readyState || ''),
                    title: String(document.title || ''),
                    appExists: !!app,
                    appChildCount: app ? app.childElementCount : -1,
                    appTextLength: app ? String(app.textContent || '').trim().length : -1,
                    bootStarted: !!window.__edumindBootStarted,
                    bootMounted: !!window.__edumindBootMounted,
                    bootTrace: Array.isArray(window.__edumindBootTrace) ? window.__edumindBootTrace.slice(-12) : [],
                    moduleScriptSrc: (function() {
                      var node = document.querySelector('script[src]');
                      return node ? String(node.getAttribute('src') || '') : '<missing>';
                    })(),
                    bodyChildCount: document.body ? document.body.childElementCount : -1
                  };
                  post('probe', JSON.stringify(payload));
                  return payload;
                } catch (e) {
                  post('probe.error', (e && (e.stack || e.message)) || String(e));
                  return null;
                }
              };
              window.addEventListener('error', function(e) {
                post('window.error', (e && e.message) || 'Unknown error');
              });
              window.addEventListener('unhandledrejection', function(e) {
                post('unhandledrejection', (e && e.reason && (e.reason.stack || e.reason.message)) || String(e && e.reason || 'Unknown rejection'));
              });
            })();
        """

        static let mountWatchdogScript = """
            (function() {
              function renderBootHint(reason) {
                try {
                  var app = document.getElementById('app');
                  if (!app) return;
                  if (app.childElementCount > 0 || app.textContent.trim().length > 0) return;
                  var panel = document.createElement('div');
                  panel.style.cssText = [
                    'margin:16px',
                    'padding:16px',
                    'border-radius:14px',
                    'background:#fff7ed',
                    'border:1px solid #fdba74',
                    'color:#9a3412',
                    'font-family:-apple-system,BlinkMacSystemFont,sans-serif',
                    'line-height:1.6'
                  ].join(';');
                  panel.innerHTML =
                    '<h3 style="margin:0 0 8px;">页面未完成挂载</h3>' +
                    '<div style="font-size:14px;">' + reason + '</div>' +
                    '<div style="margin-top:8px;font-size:12px;white-space:pre-wrap;">请检查 Xcode 控制台中的 [EduMindWeb] 日志。</div>';
                  app.appendChild(panel);
                  if (window.webkit && window.webkit.messageHandlers && window.webkit.messageHandlers.edumindLog) {
                    window.webkit.messageHandlers.edumindLog.postMessage({
                      level: 'mount.watchdog',
                      payload: reason
                    });
                  }
                } catch (e) {}
              }

              window.setTimeout(function() {
                try {
                  var app = document.getElementById('app');
                  if (!app) {
                    renderBootHint('index.html 已加载，但页面缺少 #app 节点。');
                    return;
                  }
                  if (app.childElementCount > 0 || app.textContent.trim().length > 0) return;
                  var script = document.querySelector('script[src]');
                  var scriptSrc = script ? (script.getAttribute('src') || '<inline>') : '<missing>';
                  renderBootHint('根节点仍为空，前端脚本可能未执行。script src=' + scriptSrc);
                } catch (e) {
                  renderBootHint('挂载检查异常：' + (e && (e.stack || e.message) || String(e)));
                }
              }, 2500);
            })();
        """

        private var loadTimeoutWorkItem: DispatchWorkItem?
        private var probeWorkItems: [DispatchWorkItem] = []
        private weak var webView: WKWebView?
        private var pendingVideoPickerRequestId: String?
        private var pendingVideoPickerPayload: [String: Any] = [:]
        private var activeOfflineTasks: [String: Task<Void, Never>] = [:]

        private func offlineVideoManifest() -> [String: String] {
            UserDefaults.standard.dictionary(forKey: Self.offlineVideoManifestKey) as? [String: String] ?? [:]
        }

        private func saveOfflineVideoManifest(_ manifest: [String: String]) {
            UserDefaults.standard.set(manifest, forKey: Self.offlineVideoManifestKey)
        }

        private func persistOfflineVideoURL(taskId: String, videoURL: URL) {
            guard !taskId.isEmpty else { return }
            var manifest = offlineVideoManifest()
            manifest[taskId] = videoURL.path
            saveOfflineVideoManifest(manifest)
            EduMindLog.info("OfflineVideo", "taskId=\(taskId) stored path=\(videoURL.path)")
        }

        private func resolveOfflineVideoURL(taskId: String) -> URL? {
            guard !taskId.isEmpty else { return nil }
            let manifest = offlineVideoManifest()
            guard let path = manifest[taskId], !path.isEmpty else { return nil }
            let url = URL(fileURLWithPath: path)
            guard FileManager.default.fileExists(atPath: url.path) else {
                var nextManifest = manifest
                nextManifest.removeValue(forKey: taskId)
                saveOfflineVideoManifest(nextManifest)
                EduMindLog.notice("OfflineVideo", "taskId=\(taskId) missing file path=\(path)")
                return nil
            }
            return url
        }

        private func mimeType(for fileURL: URL) -> String {
            let ext = fileURL.pathExtension.lowercased()
            if let type = UTType(filenameExtension: ext), let mimeType = type.preferredMIMEType {
                return mimeType
            }
            return "video/mp4"
        }

        private func parseByteRange(_ rangeHeader: String, totalLength: Int64) -> (start: Int64, end: Int64)? {
            let normalized = rangeHeader.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
            guard normalized.hasPrefix("bytes=") else { return nil }
            let rawRange = normalized.replacingOccurrences(of: "bytes=", with: "")
            let parts = rawRange.split(separator: "-", maxSplits: 1).map(String.init)
            guard parts.count == 2 else { return nil }

            if parts[0].isEmpty {
                guard let suffixLength = Int64(parts[1]), suffixLength > 0 else { return nil }
                let clampedLength = min(suffixLength, totalLength)
                return (max(0, totalLength - clampedLength), max(0, totalLength - 1))
            }

            guard let start = Int64(parts[0]), start >= 0 else { return nil }
            let end = Int64(parts[1]) ?? (totalLength - 1)
            guard start <= end else { return nil }
            return (start, min(end, totalLength - 1))
        }

        private func respondWithOfflineVideo(
            requestURL: URL,
            videoURL: URL,
            byteRangeHeader: String?,
            to urlSchemeTask: WKURLSchemeTask
        ) throws {
            let attributes = try FileManager.default.attributesOfItem(atPath: videoURL.path)
            let totalLength = (attributes[.size] as? NSNumber)?.int64Value ?? 0
            let mimeType = mimeType(for: videoURL)
            let selectedRange = byteRangeHeader.flatMap { parseByteRange($0, totalLength: totalLength) }
            let start = selectedRange?.start ?? 0
            let end = selectedRange?.end ?? max(0, totalLength - 1)
            let contentLength = max(0, end - start + 1)
            let statusCode = selectedRange == nil ? 200 : 206

            var headers: [String: String] = [
                "Content-Type": mimeType,
                "Accept-Ranges": "bytes",
                "Content-Length": "\(contentLength)",
                "Cache-Control": "no-store"
            ]
            if statusCode == 206 {
                headers["Content-Range"] = "bytes \(start)-\(end)/\(totalLength)"
            }

            guard let response = HTTPURLResponse(
                url: requestURL,
                statusCode: statusCode,
                httpVersion: "HTTP/1.1",
                headerFields: headers
            ) else {
                throw NSError(domain: NSURLErrorDomain, code: NSURLErrorCannotDecodeContentData)
            }

            let handle = try FileHandle(forReadingFrom: videoURL)
            defer {
                try? handle.close()
            }

            try handle.seek(toOffset: UInt64(start))
            urlSchemeTask.didReceive(response)

            var remaining = contentLength
            let chunkSize = 256 * 1024
            while remaining > 0 {
                let nextChunk = Int(min(Int64(chunkSize), remaining))
                let data = try handle.read(upToCount: nextChunk) ?? Data()
                if data.isEmpty { break }
                urlSchemeTask.didReceive(data)
                remaining -= Int64(data.count)
            }

            urlSchemeTask.didFinish()
            EduMindLog.info(
                "OfflineVideo",
                "served taskUrl=\(requestURL.absoluteString) file=\(videoURL.lastPathComponent) status=\(statusCode) bytes=\(start)-\(end)"
            )
        }

        func attach(webView: WKWebView) {
            self.webView = webView
        }

        func startLoadTimeout(for webView: WKWebView) {
            loadTimeoutWorkItem?.cancel()
            EduMindLog.info("Lifecycle", "start load timeout watchdog")
            EduMindLog.debug("Lifecycle", "watchdog target=\(String(describing: webView.url?.absoluteString ?? "<pending>"))")
            let work = DispatchWorkItem { [weak self, weak webView] in
                guard let webView else { return }
                EduMindLog.error("Lifecycle", "load timeout watchdog fired")
                self?.showErrorPage(
                    in: webView,
                    code: .navigationTimeout,
                    title: "页面加载超时",
                    details: "页面在预期时间内未完成加载，请检查前端资源是否已经同步到 App 包内。",
                    recovery: "请执行：bash ios-app/sync_ios_web_assets.sh；若仍失败，再检查 WebAssets/index.html、index.js、index.css 是否在 App 包内。"
                )
            }
            loadTimeoutWorkItem = work
            DispatchQueue.main.asyncAfter(deadline: .now() + 6, execute: work)
        }

        private func finishLoad() {
            loadTimeoutWorkItem?.cancel()
            loadTimeoutWorkItem = nil
            EduMindLog.info("Lifecycle", "finish load timeout watchdog")
        }

        private func scheduleBootProbes(for webView: WKWebView) {
            probeWorkItems.forEach { $0.cancel() }
            probeWorkItems.removeAll()

            let delays: [TimeInterval] = [0.2, 1.0, 2.5]
            EduMindLog.debug("Probe", "schedule boot probes delays=\(delays.map { String($0) }.joined(separator: ","))")
            for delay in delays {
                let work = DispatchWorkItem { [weak self, weak webView] in
                    guard let self, let webView else { return }
                    self.runProbe(in: webView, stage: "didFinish+\(delay)s")
                }
                probeWorkItems.append(work)
                DispatchQueue.main.asyncAfter(deadline: .now() + delay, execute: work)
            }
        }

        private func runProbe(in webView: WKWebView, stage: String) {
            let escapedStage = stage.replacingOccurrences(of: "'", with: "\\'")
            EduMindLog.debug("Probe", "run probe stage=\(stage)")
            let js = """
            (function() {
              try {
                if (!window.__edumindNativeProbe) return 'null';
                return JSON.stringify(window.__edumindNativeProbe('\(escapedStage)'));
              } catch (e) {
                return JSON.stringify({
                  stage: '\(escapedStage)',
                  probeError: String((e && (e.stack || e.message)) || e)
                });
              }
            })();
            """
            webView.evaluateJavaScript(js) { result, error in
                if let error {
                    EduMindLog.error("Probe", "stage=\(stage) error=\(error.localizedDescription)")
                    return
                }
                EduMindLog.info("Probe", "stage=\(stage) payload=\(String(describing: result ?? "<nil>"))")
            }
        }

        private func nativeLogLevel(for level: String) -> EduMindLogLevel {
            switch level {
            case "console.debug":
                return .debug
            case "console.info", "probe", "probe.native", "lifecycle.info":
                return .info
            case "console.log", "mount.watchdog":
                return .notice
            case "console.warn":
                return .notice
            case "console.error", "window.error", "unhandledrejection", "probe.error":
                return .error
            default:
                return .notice
            }
        }

        private func nativeBridgeCapabilities() -> [String: Any] {
            [
                "platform": "ios",
                "bridgeVersion": 1,
                "supportsOfflineTranscription": true,
                "supportsNativeVideoPicker": true,
                "supportsPageStateReporting": true,
                "pageStateHandlerName": Self.pageStateHandlerName,
                "transcriptionEngine": "whisper_cpp_on_device_with_apple_speech_fallback",
                "supportsOnDeviceWhisper": true,
                "supportsBackendWhisperFallback": true,
                "requiresSpeechAuthorization": true,
                "availableActions": [
                    "ping",
                    "getCapabilities",
                    "startOfflineTranscription"
                ]
            ]
        }

        private func jsonString(from value: Any) -> String {
            guard JSONSerialization.isValidJSONObject(value),
                  let data = try? JSONSerialization.data(withJSONObject: value, options: [.sortedKeys]),
                  let text = String(data: data, encoding: .utf8)
            else {
                return String(describing: value)
            }
            return text
        }

        private func firstString(in payload: [String: Any], keys: [String]) -> String {
            for key in keys {
                let rawValue = payload[key]
                let text = String(describing: rawValue ?? "").trimmingCharacters(in: .whitespacesAndNewlines)
                if !text.isEmpty, text != "<null>" {
                    return text
                }
            }
            return ""
        }

        private func firstBool(in payload: [String: Any], keys: [String]) -> Bool? {
            for key in keys {
                guard let rawValue = payload[key] else { continue }
                if let boolValue = rawValue as? Bool {
                    return boolValue
                }
                let text = String(describing: rawValue).trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
                switch text {
                case "true", "1", "yes", "on":
                    return true
                case "false", "0", "no", "off":
                    return false
                default:
                    continue
                }
            }
            return nil
        }

        private func handlePageStateMessage(_ body: Any) {
            guard let payload = body as? [String: Any] else {
                EduMindLog.notice("PageState", "received non-object page state payload: \(String(describing: body))")
                return
            }

            let route = firstString(in: payload, keys: ["route", "path", "href"])
            let pageName = firstString(in: payload, keys: ["pageName", "page", "name"])
            let businessId = firstString(in: payload, keys: ["businessId", "videoId", "noteId", "taskId", "id"])
            let stage = firstString(in: payload, keys: ["stage", "status"])
            let mounted = firstBool(in: payload, keys: ["mounted", "isMounted"])
            EduMindLog.info(
                "PageState",
                "route=\(route.isEmpty ? "<unknown>" : route) page=\(pageName.isEmpty ? "<unknown>" : pageName) businessId=\(businessId.isEmpty ? "<none>" : businessId) mounted=\(mounted.map(String.init) ?? "<unknown>") stage=\(stage.isEmpty ? "<none>" : stage) payload=\(jsonString(from: payload))"
            )
        }

        private func respondToNativeRequest(
            requestId: String,
            success: Bool,
            payload: [String: Any] = [:],
            errorMessage: String? = nil
        ) {
            var responseBody: [String: Any] = [
                "requestId": requestId,
                "success": success,
                "payload": payload
            ]
            responseBody["error"] = errorMessage ?? NSNull()

            guard
                let webView,
                let data = try? JSONSerialization.data(
                    withJSONObject: responseBody,
                    options: []
                ),
                let json = String(data: data, encoding: .utf8)
            else {
                EduMindLog.error("Bridge", "failed to serialize native bridge response for requestId=\(requestId)")
                return
            }

            let js = """
            (function() {
              if (typeof window.__edumindHandleNativeResponse === 'function') {
                window.__edumindHandleNativeResponse(\(json));
              }
            })();
            """
            DispatchQueue.main.async {
                webView.evaluateJavaScript(js) { _, error in
                    if let error {
                        EduMindLog.error("Bridge", "native response delivery failed requestId=\(requestId) error=\(error.localizedDescription)")
                    }
                }
            }
        }

        private func sendNativeEvent(name: String, payload: [String: Any]) {
            guard
                let webView,
                let data = try? JSONSerialization.data(withJSONObject: payload, options: []),
                let json = String(data: data, encoding: .utf8)
            else {
                EduMindLog.error("Bridge", "failed to serialize native event payload name=\(name)")
                return
            }

            let escapedName = name
                .replacingOccurrences(of: "\\", with: "\\\\")
                .replacingOccurrences(of: "'", with: "\\'")

            let js = """
            (function() {
              if (typeof window.__edumindReceiveNativeEvent === 'function') {
                window.__edumindReceiveNativeEvent('\(escapedName)', \(json));
              }
            })();
            """
            DispatchQueue.main.async {
                webView.evaluateJavaScript(js) { _, error in
                    if let error {
                        EduMindLog.error("Bridge", "native event delivery failed name=\(name) error=\(error.localizedDescription)")
                    }
                }
            }
        }

        private func topViewController() -> UIViewController? {
            if let root = webView?.window?.rootViewController {
                var current: UIViewController? = root
                while let presented = current?.presentedViewController {
                    current = presented
                }
                return current
            }

            let root = UIApplication.shared.connectedScenes
                .compactMap { $0 as? UIWindowScene }
                .flatMap(\.windows)
                .first(where: \.isKeyWindow)?
                .rootViewController

            var current = root
            while let presented = current?.presentedViewController {
                current = presented
            }
            return current
        }

        private func normalizeSpeechLocaleIdentifier(from payload: [String: Any]) -> String {
            let source = payload["locale"] ?? payload["language"] ?? ""
            let raw = String(describing: source).trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
            if raw.isEmpty || raw == "auto" {
                return Locale.preferredLanguages.first ?? "zh-CN"
            }

            switch raw {
            case "other", "zh", "zh-cn", "zh_hans", "zh-hans", "chinese", "中文", "中文/其他":
                return "zh-CN"
            case "yue", "yue-cn", "粤语":
                return "yue-CN"
            case "wuu", "wuu-cn", "吴语":
                return "wuu-CN"
            case "zh-tw", "zh_hant", "zh-hant", "繁体中文":
                return "zh-TW"
            case "en", "en-us", "english", "英文":
                return "en-US"
            case "ja", "ja-jp", "japanese", "日文":
                return "ja-JP"
            default:
                return raw
            }
        }

        private func createWorkingDirectory() throws -> URL {
            let base = FileManager.default.urls(for: .cachesDirectory, in: .userDomainMask).first
                ?? FileManager.default.temporaryDirectory
            let dir = base.appendingPathComponent("OfflineTranscription", isDirectory: true)
            try FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
            return dir
        }

        private func copySelectedVideoToWorkingDirectory(from sourceURL: URL) throws -> URL {
            let dir = try createWorkingDirectory()
            let ext = sourceURL.pathExtension.isEmpty ? "mov" : sourceURL.pathExtension.lowercased()
            let destinationURL = dir.appendingPathComponent("\(UUID().uuidString).\(ext)")
            if FileManager.default.fileExists(atPath: destinationURL.path) {
                try FileManager.default.removeItem(at: destinationURL)
            }
            try FileManager.default.copyItem(at: sourceURL, to: destinationURL)
            return destinationURL
        }

        private func buildSelectedVideoMetadata(from sourceURL: URL) throws -> NativeSelectedVideo {
            let workingURL = try copySelectedVideoToWorkingDirectory(from: sourceURL)
            let values = try workingURL.resourceValues(forKeys: [.nameKey, .fileSizeKey])
            let fileName = values.name ?? sourceURL.lastPathComponent
            let fileSize = values.fileSize ?? 0
            let fileExt = workingURL.pathExtension.lowercased()
            return NativeSelectedVideo(
                taskId: UUID().uuidString,
                workingURL: workingURL,
                fileName: fileName,
                fileSize: fileSize,
                fileExt: fileExt
            )
        }

        private func startOfflineTranscriptionFlow(requestId: String, payload: [String: Any]) {
            guard pendingVideoPickerRequestId == nil else {
                respondToNativeRequest(
                    requestId: requestId,
                    success: false,
                    errorMessage: NativeOfflineTranscriptionError.pickerBusy.localizedDescription
                )
                return
            }

            guard activeOfflineTasks.isEmpty else {
                respondToNativeRequest(
                    requestId: requestId,
                    success: false,
                    errorMessage: NativeOfflineTranscriptionError.transcriptionBusy.localizedDescription
                )
                return
            }

            guard let presenter = topViewController() else {
                respondToNativeRequest(
                    requestId: requestId,
                    success: false,
                    errorMessage: NativeOfflineTranscriptionError.presenterUnavailable.localizedDescription
                )
                return
            }

            pendingVideoPickerRequestId = requestId
            pendingVideoPickerPayload = payload

            let picker = UIDocumentPickerViewController(
                forOpeningContentTypes: [UTType.movie, UTType.video],
                asCopy: true
            )
            picker.delegate = self
            picker.allowsMultipleSelection = false
            presenter.present(picker, animated: true)
        }

        private func clearPendingVideoPickerState() {
            pendingVideoPickerRequestId = nil
            pendingVideoPickerPayload = [:]
        }

        private func offlineProgressBar(_ progress: Int, width: Int = 16) -> String {
            let clamped = max(0, min(100, progress))
            let filled = Int(round((Double(clamped) / 100.0) * Double(width)))
            let fullBlocks = String(repeating: "█", count: max(0, min(width, filled)))
            let emptyBlocks = String(repeating: "░", count: max(0, width - filled))
            return "[\(fullBlocks)\(emptyBlocks)] \(String(format: "%3d%%", clamped))"
        }

        private func sendOfflineProgressEvent(
            taskId: String,
            fileName: String,
            fileSize: Int,
            phase: String,
            progress: Int,
            message: String,
            localeIdentifier: String = "",
            engine: String = "apple_speech_on_device"
        ) {
            EduMindLog.info(
                "OfflineTranscription",
                "\(offlineProgressBar(progress)) taskId=\(taskId) phase=\(phase) engine=\(engine) locale=\(localeIdentifier.isEmpty ? "<auto>" : localeIdentifier) message=\(message)"
            )
            sendNativeEvent(name: "offline-transcription-progress", payload: [
                "taskId": taskId,
                "fileName": fileName,
                "fileSize": fileSize,
                "phase": phase,
                "status": phase,
                "progress": progress,
                "message": message,
                "locale": localeIdentifier,
                "engine": engine
            ])
        }

        private func sendOfflineFailureEvent(
            taskId: String,
            fileName: String,
            fileSize: Int,
            message: String,
            engine: String = "apple_speech_on_device"
        ) {
            EduMindLog.error(
                "OfflineTranscription",
                "\(offlineProgressBar(0)) taskId=\(taskId) phase=failed engine=\(engine) message=\(message)"
            )
            sendNativeEvent(name: "offline-transcription-failed", payload: [
                "taskId": taskId,
                "fileName": fileName,
                "fileSize": fileSize,
                "status": "failed",
                "progress": 0,
                "message": message,
                "engine": engine
            ])
        }

        private func currentAPIBaseURL() -> URL? {
            let configuredAPIBase = (
                Bundle.main.object(forInfoDictionaryKey: "EDUMIND_API_BASE_URL") as? String
            )?
                .trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
            let apiBase = configuredAPIBase.isEmpty ? "http://yuandeMacBook-Pro.local:2004" : configuredAPIBase
            return URL(string: apiBase.trimmingCharacters(in: .whitespacesAndNewlines))
        }

        private func resolvedOnDeviceWhisperModel(
            localeIdentifier: String,
            payload: [String: Any]
        ) -> String {
            let requestedModel = firstString(in: payload, keys: ["whisperModel", "model"]).lowercased()
            return EduMindOnDeviceWhisperSession.resolveModelName(
                requestedModel: requestedModel,
                localeIdentifier: localeIdentifier
            )
        }

        private func transcribeAudioFileWithOnDeviceWhisper(
            taskId: String,
            audioURL: URL,
            fileName: String,
            fileSize: Int,
            localeIdentifier: String,
            payload: [String: Any]
        ) async throws -> NativeTranscriptionResult {
            let requestedLanguage = firstString(in: payload, keys: ["language", "locale"])
            let effectiveModel = resolvedOnDeviceWhisperModel(localeIdentifier: localeIdentifier, payload: payload)

            sendOfflineProgressEvent(
                taskId: taskId,
                fileName: fileName,
                fileSize: fileSize,
                phase: "transcribing",
                progress: 58,
                message: "正在检查本机 Whisper 离线模型（\(effectiveModel)）",
                localeIdentifier: localeIdentifier,
                engine: "whisper_cpp_on_device"
            )

            let modelURL: URL
            do {
                modelURL = try await EduMindOnDeviceWhisperSession.ensureModel(named: effectiveModel)
            } catch {
                throw NativeOfflineTranscriptionError.onDeviceWhisperUnavailable
            }

            sendOfflineProgressEvent(
                taskId: taskId,
                fileName: fileName,
                fileSize: fileSize,
                phase: "transcribing",
                progress: 66,
                message: "本机 Whisper 模型已就绪，开始离线转录（\(effectiveModel)）",
                localeIdentifier: localeIdentifier,
                engine: "whisper_cpp_on_device"
            )

            let session: EduMindOnDeviceWhisperSession
            do {
                session = try EduMindOnDeviceWhisperSession(modelURL: modelURL, effectiveModel: effectiveModel)
            } catch {
                throw NativeOfflineTranscriptionError.onDeviceWhisperUnavailable
            }

            let chunks = try await buildAudioChunks(audioURL: audioURL, taskId: taskId)
            var mergedText = ""
            var mergedSegments: [[String: Any]] = []

            for chunk in chunks {
                let chunkLabel = chunks.count > 1 ? "（\(chunk.index + 1)/\(chunk.total)）" : ""
                let progressBase = 70 + Int((Double(chunk.index) / Double(max(chunk.total, 1))) * 20)
                sendOfflineProgressEvent(
                    taskId: taskId,
                    fileName: fileName,
                    fileSize: fileSize,
                    phase: "transcribing",
                    progress: progressBase,
                    message: "正在使用本机 Whisper 离线识别\(chunkLabel)",
                    localeIdentifier: localeIdentifier,
                    engine: "whisper_cpp_on_device"
                )

                let chunkResult = try session.transcribeChunk(
                    audioURL: chunk.url,
                    chunkStartSeconds: chunk.startSeconds,
                    localeIdentifier: localeIdentifier,
                    requestedLanguage: requestedLanguage
                )

                if !chunkResult.text.isEmpty {
                    mergedText = mergeTranscriptionText(mergedText, chunkResult.text)
                }
                mergedSegments.append(contentsOf: chunkResult.segments.map { segment in
                    [
                        "text": segment.text,
                        "start": segment.start,
                        "duration": segment.duration,
                        "confidence": segment.confidence
                    ]
                })

                if chunk.requiresCleanup {
                    try? FileManager.default.removeItem(at: chunk.url)
                }
            }

            let finalText = mergedText.trimmingCharacters(in: .whitespacesAndNewlines)
            guard !finalText.isEmpty else {
                throw NativeOfflineTranscriptionError.emptyTranscript
            }

            return NativeTranscriptionResult(
                text: finalText,
                segments: mergedSegments,
                localeIdentifier: localeIdentifier,
                engine: "whisper_cpp_on_device"
            )
        }

        private func makeMultipartBody(
            boundary: String,
            fileURL: URL,
            fieldName: String,
            fileName: String,
            mimeType: String,
            formFields: [String: String]
        ) throws -> Data {
            var body = Data()
            let lineBreak = "\r\n"

            for (key, value) in formFields {
                body.append(Data("--\(boundary)\(lineBreak)".utf8))
                body.append(Data("Content-Disposition: form-data; name=\"\(key)\"\(lineBreak)\(lineBreak)".utf8))
                body.append(Data("\(value)\(lineBreak)".utf8))
            }

            body.append(Data("--\(boundary)\(lineBreak)".utf8))
            body.append(
                Data(
                    "Content-Disposition: form-data; name=\"\(fieldName)\"; filename=\"\(fileName)\"\(lineBreak)".utf8
                )
            )
            body.append(Data("Content-Type: \(mimeType)\(lineBreak)\(lineBreak)".utf8))
            body.append(try Data(contentsOf: fileURL))
            body.append(Data(lineBreak.utf8))
            body.append(Data("--\(boundary)--\(lineBreak)".utf8))
            return body
        }

        private func requestSpeechAuthorization() async -> SFSpeechRecognizerAuthorizationStatus {
            await withCheckedContinuation { continuation in
                SFSpeechRecognizer.requestAuthorization { status in
                    continuation.resume(returning: status)
                }
            }
        }

        private func exportAudioTrack(from videoURL: URL, taskId: String) async throws -> URL {
            let asset = AVURLAsset(url: videoURL)
            guard let exportSession = AVAssetExportSession(asset: asset, presetName: AVAssetExportPresetAppleM4A) else {
                throw NativeOfflineTranscriptionError.audioExtractionUnavailable
            }

            let workingDirectory = try createWorkingDirectory()
            let outputURL = workingDirectory.appendingPathComponent("\(taskId).m4a")
            if FileManager.default.fileExists(atPath: outputURL.path) {
                try FileManager.default.removeItem(at: outputURL)
            }

            exportSession.outputURL = outputURL
            exportSession.outputFileType = .m4a
            exportSession.shouldOptimizeForNetworkUse = false

            return try await withCheckedThrowingContinuation { continuation in
                exportSession.exportAsynchronously {
                    switch exportSession.status {
                    case .completed:
                        continuation.resume(returning: outputURL)
                    case .failed:
                        continuation.resume(throwing: exportSession.error ?? NativeOfflineTranscriptionError.audioExtractionUnavailable)
                    case .cancelled:
                        continuation.resume(throwing: NativeOfflineTranscriptionError.pickerCancelled)
                    default:
                        continuation.resume(throwing: exportSession.error ?? NativeOfflineTranscriptionError.audioExtractionUnavailable)
                    }
                }
            }
        }

        private func exportAudioChunk(
            from audioURL: URL,
            taskId: String,
            chunkIndex: Int,
            startSeconds: Double,
            durationSeconds: Double
        ) async throws -> URL {
            let asset = AVURLAsset(url: audioURL)
            guard let exportSession = AVAssetExportSession(asset: asset, presetName: AVAssetExportPresetAppleM4A) else {
                throw NativeOfflineTranscriptionError.audioExtractionUnavailable
            }

            let workingDirectory = try createWorkingDirectory()
            let outputURL = workingDirectory.appendingPathComponent("\(taskId)-chunk-\(chunkIndex).m4a")
            if FileManager.default.fileExists(atPath: outputURL.path) {
                try FileManager.default.removeItem(at: outputURL)
            }

            exportSession.outputURL = outputURL
            exportSession.outputFileType = .m4a
            exportSession.shouldOptimizeForNetworkUse = false
            exportSession.timeRange = CMTimeRange(
                start: CMTime(seconds: startSeconds, preferredTimescale: 600),
                duration: CMTime(seconds: durationSeconds, preferredTimescale: 600)
            )

            return try await withCheckedThrowingContinuation { continuation in
                exportSession.exportAsynchronously {
                    switch exportSession.status {
                    case .completed:
                        continuation.resume(returning: outputURL)
                    case .failed:
                        continuation.resume(throwing: exportSession.error ?? NativeOfflineTranscriptionError.audioExtractionUnavailable)
                    case .cancelled:
                        continuation.resume(throwing: NativeOfflineTranscriptionError.pickerCancelled)
                    default:
                        continuation.resume(throwing: exportSession.error ?? NativeOfflineTranscriptionError.audioExtractionUnavailable)
                    }
                }
            }
        }

        private func normalizeAudioForSpeechRecognition(
            sourceURL: URL,
            taskId: String,
            chunkIndex: Int
        ) throws -> URL {
            let inputFile = try AVAudioFile(forReading: sourceURL)
            guard let outputFormat = AVAudioFormat(
                commonFormat: .pcmFormatInt16,
                sampleRate: 16_000,
                channels: 1,
                interleaved: false
            ) else {
                throw NativeOfflineTranscriptionError.audioExtractionUnavailable
            }
            guard let converter = AVAudioConverter(from: inputFile.processingFormat, to: outputFormat) else {
                throw NativeOfflineTranscriptionError.audioExtractionUnavailable
            }

            converter.sampleRateConverterQuality = AVAudioQuality.max.rawValue

            let workingDirectory = try createWorkingDirectory()
            let outputURL = workingDirectory.appendingPathComponent("\(taskId)-speech-\(chunkIndex).caf")
            if FileManager.default.fileExists(atPath: outputURL.path) {
                try FileManager.default.removeItem(at: outputURL)
            }

            let outputFile = try AVAudioFile(
                forWriting: outputURL,
                settings: outputFormat.settings,
                commonFormat: outputFormat.commonFormat,
                interleaved: outputFormat.isInterleaved
            )

            let inputFrameCapacity: AVAudioFrameCount = 8_192
            let ratio = outputFormat.sampleRate / max(inputFile.processingFormat.sampleRate, 1)
            let outputFrameCapacity = AVAudioFrameCount(max(4_096, Int(Double(inputFrameCapacity) * ratio) + 1_024))

            while true {
                guard let inputBuffer = AVAudioPCMBuffer(
                    pcmFormat: inputFile.processingFormat,
                    frameCapacity: inputFrameCapacity
                ) else {
                    throw NativeOfflineTranscriptionError.audioExtractionUnavailable
                }
                try inputFile.read(into: inputBuffer)
                if inputBuffer.frameLength == 0 {
                    break
                }

                guard let outputBuffer = AVAudioPCMBuffer(
                    pcmFormat: outputFormat,
                    frameCapacity: outputFrameCapacity
                ) else {
                    throw NativeOfflineTranscriptionError.audioExtractionUnavailable
                }

                var conversionError: NSError?
                let status = converter.convert(to: outputBuffer, error: &conversionError) { _, outStatus in
                    outStatus.pointee = .haveData
                    return inputBuffer
                }

                if let conversionError {
                    throw conversionError
                }
                if status == .error {
                    throw NativeOfflineTranscriptionError.audioExtractionUnavailable
                }
                if outputBuffer.frameLength > 0 {
                    try outputFile.write(from: outputBuffer)
                }
            }

            EduMindLog.info(
                "OfflineTranscription",
                "taskId=\(taskId) prepared speech audio chunk=\(chunkIndex + 1) sourceRate=\(String(format: "%.0f", inputFile.processingFormat.sampleRate))Hz sourceChannels=\(inputFile.processingFormat.channelCount) targetRate=16000Hz targetChannels=1"
            )
            return outputURL
        }

        private func buildAudioChunks(audioURL: URL, taskId: String) async throws -> [NativeAudioChunk] {
            let asset = AVURLAsset(url: audioURL)
            let loadedDuration = try await asset.load(.duration)
            let duration = CMTimeGetSeconds(loadedDuration)
            let safeDuration = duration.isFinite && duration > 0 ? duration : 0

            guard safeDuration > offlineChunkDurationSeconds else {
                return [
                    NativeAudioChunk(
                        index: 0,
                        total: 1,
                        startSeconds: 0,
                        durationSeconds: max(safeDuration, offlineMinimumChunkSeconds),
                        url: audioURL,
                        requiresCleanup: false
                    )
                ]
            }

            let stepSeconds = max(offlineChunkDurationSeconds - offlineChunkOverlapSeconds, offlineMinimumChunkSeconds)
            var rawChunks: [(start: Double, duration: Double, url: URL)] = []
            var startSeconds = 0.0
            var chunkIndex = 0

            while startSeconds < safeDuration {
                let remaining = safeDuration - startSeconds
                let durationSeconds = max(min(offlineChunkDurationSeconds, remaining), offlineMinimumChunkSeconds)
                let chunkURL = try await exportAudioChunk(
                    from: audioURL,
                    taskId: taskId,
                    chunkIndex: chunkIndex,
                    startSeconds: startSeconds,
                    durationSeconds: durationSeconds
                )
                rawChunks.append((
                    start: startSeconds,
                    duration: durationSeconds,
                    url: chunkURL
                ))
                if startSeconds + durationSeconds >= safeDuration {
                    break
                }
                startSeconds += stepSeconds
                chunkIndex += 1
            }

            let chunkCount = rawChunks.count
            let chunks = rawChunks.enumerated().map { index, chunk in
                NativeAudioChunk(
                    index: index,
                    total: chunkCount,
                    startSeconds: chunk.start,
                    durationSeconds: chunk.duration,
                    url: chunk.url,
                    requiresCleanup: true
                )
            }

            EduMindLog.info(
                "OfflineTranscription",
                "taskId=\(taskId) audioDuration=\(String(format: "%.2f", safeDuration))s chunkDuration=\(String(format: "%.1f", offlineChunkDurationSeconds))s overlap=\(String(format: "%.1f", offlineChunkOverlapSeconds))s chunks=\(chunkCount)"
            )
            return chunks
        }

        private func mergeTranscriptionText(_ existingText: String, _ nextText: String) -> String {
            let left = existingText.trimmingCharacters(in: .whitespacesAndNewlines)
            let right = nextText.trimmingCharacters(in: .whitespacesAndNewlines)

            if left.isEmpty { return right }
            if right.isEmpty { return left }
            if left.hasSuffix(right) { return left }
            if right.hasPrefix(left) { return right }

            let leftChars = Array(left)
            let rightChars = Array(right)
            let maxOverlap = min(48, min(leftChars.count, rightChars.count))

            if maxOverlap >= 4 {
                for length in stride(from: maxOverlap, through: 4, by: -1) {
                    if Array(leftChars.suffix(length)) == Array(rightChars.prefix(length)) {
                        return left + String(rightChars.dropFirst(length))
                    }
                }
            }

            let suffixSample = String(leftChars.suffix(min(8, leftChars.count)))
            let prefixSample = String(rightChars.prefix(min(8, rightChars.count)))
            if !suffixSample.isEmpty, suffixSample == prefixSample {
                return left + String(rightChars.dropFirst(suffixSample.count))
            }

            return left + "\n" + right
        }

        private func isNoSpeechDetectedError(_ error: Error) -> Bool {
            let message = error.localizedDescription.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
            return message.contains("no speech detected") || message.contains("未检测到语音")
        }

        private func buildSpeechRecognizer(localeIdentifier: String) throws -> SFSpeechRecognizer {
            let fallbackCandidates: [String]
            switch localeIdentifier.lowercased() {
            case "yue-cn":
                fallbackCandidates = ["yue-CN", "zh-HK", "zh-CN", "zh-TW"]
            case "wuu-cn":
                fallbackCandidates = ["wuu-CN", "zh-CN", "zh-HK"]
            case "zh-tw":
                fallbackCandidates = ["zh-TW", "zh-HK", "zh-CN"]
            case "en-us":
                fallbackCandidates = ["en-US", "en-GB"]
            default:
                fallbackCandidates = [localeIdentifier, Locale.preferredLanguages.first ?? "", "zh-CN", "en-US"]
            }
            let candidates = Array(NSOrderedSet(array: fallbackCandidates.filter { !$0.isEmpty })) as? [String] ?? fallbackCandidates.filter { !$0.isEmpty }
            var firstRecognizer: SFSpeechRecognizer?
            var inspectedCandidates: [String] = []

            for candidate in candidates {
                if let recognizer = SFSpeechRecognizer(locale: Locale(identifier: candidate)) {
                    if firstRecognizer == nil {
                        firstRecognizer = recognizer
                    }
                    let supportFlag = recognizer.supportsOnDeviceRecognition ? "on-device=yes" : "on-device=no"
                    inspectedCandidates.append("\(recognizer.locale.identifier)(\(supportFlag))")
                    EduMindLog.info(
                        "OfflineTranscription",
                        "candidate recognizer locale=\(recognizer.locale.identifier) requested=\(localeIdentifier) \(supportFlag)"
                    )
                    if recognizer.supportsOnDeviceRecognition {
                        EduMindLog.info(
                            "OfflineTranscription",
                            "using recognizer locale=\(recognizer.locale.identifier) requested=\(localeIdentifier)"
                        )
                        return recognizer
                    }
                } else {
                    inspectedCandidates.append("\(candidate)(unavailable)")
                    EduMindLog.notice(
                        "OfflineTranscription",
                        "candidate recognizer unavailable locale=\(candidate) requested=\(localeIdentifier)"
                    )
                }
            }

            if firstRecognizer != nil {
                let inspectedSummary = inspectedCandidates.joined(separator: ", ")
                EduMindLog.error(
                    "OfflineTranscription",
                    "no on-device recognizer available requested=\(localeIdentifier) candidates=\(inspectedSummary)"
                )
                throw NativeOfflineTranscriptionError.onDeviceRecognitionUnavailable
            }

            let candidateSummary = candidates.joined(separator: ", ")
            EduMindLog.error(
                "OfflineTranscription",
                "no recognizer available requested=\(localeIdentifier) candidates=\(candidateSummary)"
            )
            throw NativeOfflineTranscriptionError.recognizerUnavailable
        }

        private func transcribeAudioChunk(
            recognizer: SFSpeechRecognizer,
            audioChunk: NativeAudioChunk,
            taskId: String,
            fileName: String,
            fileSize: Int
        ) async throws -> NativeTranscriptionResult {
            let chunkLabel = audioChunk.total > 1 ? "（\(audioChunk.index + 1)/\(audioChunk.total)）" : ""
            let progressBase = 55 + Int((Double(audioChunk.index) / Double(max(audioChunk.total, 1))) * 30)
            let progressPeak = min(progressBase + 25, 95)
            let chunkWindow = "start=\(String(format: "%.1f", audioChunk.startSeconds))s duration=\(String(format: "%.1f", audioChunk.durationSeconds))s"
            var preparedAudioURL: URL? = nil

            do {
                preparedAudioURL = try normalizeAudioForSpeechRecognition(
                    sourceURL: audioChunk.url,
                    taskId: taskId,
                    chunkIndex: audioChunk.index
                )
            } catch {
                EduMindLog.notice(
                    "OfflineTranscription",
                    "taskId=\(taskId) chunk=\(audioChunk.index + 1)/\(audioChunk.total) normalize-audio-failed fallback=original reason=\(error.localizedDescription)"
                )
            }

            let recognitionAudioURL = preparedAudioURL ?? audioChunk.url
            defer {
                if let preparedAudioURL {
                    try? FileManager.default.removeItem(at: preparedAudioURL)
                }
            }

            sendOfflineProgressEvent(
                taskId: taskId,
                fileName: fileName,
                fileSize: fileSize,
                phase: "transcribing",
                progress: progressBase,
                message: "正在进行本地语音识别\(chunkLabel) · \(chunkWindow)",
                localeIdentifier: recognizer.locale.identifier
            )

            let request = SFSpeechURLRecognitionRequest(url: recognitionAudioURL)
            request.requiresOnDeviceRecognition = true
            request.shouldReportPartialResults = true
            if #available(iOS 16.0, *) {
                request.addsPunctuation = true
            }
            request.taskHint = .dictation

            return try await withCheckedThrowingContinuation { continuation in
                var hasResumed = false
                var recognitionTask: SFSpeechRecognitionTask?

                recognitionTask = recognizer.recognitionTask(with: request) { [weak self] result, error in
                    guard let self else { return }

                    if let result {
                        let partialText = result.bestTranscription.formattedString.trimmingCharacters(in: .whitespacesAndNewlines)
                        if !partialText.isEmpty {
                            self.sendOfflineProgressEvent(
                                taskId: taskId,
                                fileName: fileName,
                                fileSize: fileSize,
                                phase: "transcribing",
                                progress: result.isFinal ? progressPeak : min(progressBase + 10, progressPeak - 5),
                                message: "正在进行本地语音识别\(chunkLabel) · \(chunkWindow)",
                                localeIdentifier: recognizer.locale.identifier
                            )
                        }

                        if result.isFinal && !hasResumed {
                            hasResumed = true
                            let text = partialText
                            let segments = result.bestTranscription.segments.map { segment in
                                [
                                    "text": segment.substring,
                                    "start": segment.timestamp + audioChunk.startSeconds,
                                    "duration": segment.duration,
                                    "confidence": segment.confidence
                                ]
                            }
                            if text.isEmpty {
                                continuation.resume(throwing: NativeOfflineTranscriptionError.emptyTranscript)
                            } else {
                                continuation.resume(returning: NativeTranscriptionResult(
                                    text: text,
                                    segments: segments,
                                    localeIdentifier: recognizer.locale.identifier,
                                    engine: "apple_speech_on_device"
                                ))
                            }
                            recognitionTask?.cancel()
                            recognitionTask = nil
                            return
                        }
                    }

                    if let error, !hasResumed {
                        hasResumed = true
                        continuation.resume(throwing: error)
                        recognitionTask?.cancel()
                        recognitionTask = nil
                    }
                }
            }
        }

        private func transcribeAudioFile(
            taskId: String,
            audioURL: URL,
            fileName: String,
            fileSize: Int,
            localeIdentifier: String
        ) async throws -> NativeTranscriptionResult {
            let authorizationStatus = await requestSpeechAuthorization()
            guard authorizationStatus == .authorized else {
                throw NativeOfflineTranscriptionError.speechAuthorizationDenied
            }

            let recognizer = try buildSpeechRecognizer(localeIdentifier: localeIdentifier)
            let chunks = try await buildAudioChunks(audioURL: audioURL, taskId: taskId)
            var mergedText = ""
            var chunkSegments: [[String: Any]] = []

            for chunk in chunks {
                do {
                    let chunkResult = try await transcribeAudioChunk(
                        recognizer: recognizer,
                        audioChunk: chunk,
                        taskId: taskId,
                        fileName: fileName,
                        fileSize: fileSize
                    )
                    if !chunkResult.text.isEmpty {
                        let nextMergedText = mergeTranscriptionText(mergedText, chunkResult.text)
                        if nextMergedText != mergedText {
                            mergedText = nextMergedText
                        }
                    }
                    chunkSegments.append(contentsOf: chunkResult.segments)
                } catch {
                    if isNoSpeechDetectedError(error) {
                        EduMindLog.notice(
                            "OfflineTranscription",
                            "taskId=\(taskId) skip chunk \(chunk.index + 1)/\(chunk.total) start=\(String(format: "%.2f", chunk.startSeconds))s reason=no-speech"
                        )
                    } else {
                        if chunk.requiresCleanup {
                            try? FileManager.default.removeItem(at: chunk.url)
                        }
                        throw error
                    }
                }

                if chunk.requiresCleanup {
                    try? FileManager.default.removeItem(at: chunk.url)
                }
            }

            let finalText = mergedText.trimmingCharacters(in: .whitespacesAndNewlines)

            if finalText.isEmpty {
                throw NativeOfflineTranscriptionError.emptyTranscript
            }

            return NativeTranscriptionResult(
                text: finalText,
                segments: chunkSegments,
                localeIdentifier: recognizer.locale.identifier,
                engine: "apple_speech_on_device"
            )
        }

        private func runOfflineTranscription(task: NativeSelectedVideo, payload: [String: Any]) async {
            let localeIdentifier = normalizeSpeechLocaleIdentifier(from: payload)
            let requestedLanguage = String(describing: payload["locale"] ?? payload["language"] ?? "")
            var activeEngine = "whisper_cpp_on_device"
            EduMindLog.info(
                "OfflineTranscription",
                "taskId=\(task.taskId) requestedLanguage=\(requestedLanguage) normalizedLocale=\(localeIdentifier)"
            )

            do {
                sendOfflineProgressEvent(
                    taskId: task.taskId,
                    fileName: task.fileName,
                    fileSize: task.fileSize,
                    phase: "preparing",
                    progress: 5,
                    message: "已选择本地视频，准备提取音频",
                    localeIdentifier: localeIdentifier
                )

                sendOfflineProgressEvent(
                    taskId: task.taskId,
                    fileName: task.fileName,
                    fileSize: task.fileSize,
                    phase: "extracting",
                    progress: 25,
                    message: "正在提取本地视频音频",
                    localeIdentifier: localeIdentifier
                )
                let audioURL = try await exportAudioTrack(from: task.workingURL, taskId: task.taskId)

                sendOfflineProgressEvent(
                    taskId: task.taskId,
                    fileName: task.fileName,
                    fileSize: task.fileSize,
                    phase: "transcribing",
                    progress: 55,
                    message: "音频提取完成，开始本机离线转录",
                    localeIdentifier: localeIdentifier,
                    engine: "whisper_cpp_on_device"
                )
                let transcription: NativeTranscriptionResult
                do {
                    activeEngine = "whisper_cpp_on_device"
                    EduMindLog.notice(
                        "OfflineTranscription",
                        "taskId=\(task.taskId) prefer on-device whisper for locale=\(localeIdentifier) model=\(resolvedOnDeviceWhisperModel(localeIdentifier: localeIdentifier, payload: payload))"
                    )
                    transcription = try await transcribeAudioFileWithOnDeviceWhisper(
                        taskId: task.taskId,
                        audioURL: audioURL,
                        fileName: task.fileName,
                        fileSize: task.fileSize,
                        localeIdentifier: localeIdentifier,
                        payload: payload
                    )
                } catch let error as NativeOfflineTranscriptionError where error == .onDeviceWhisperUnavailable {
                    activeEngine = "apple_speech_on_device"
                    EduMindLog.notice(
                        "OfflineTranscription",
                        "taskId=\(task.taskId) on-device-whisper-unavailable fallback=apple_speech reason=\(error.localizedDescription)"
                    )
                    transcription = try await transcribeAudioFile(
                        taskId: task.taskId,
                        audioURL: audioURL,
                        fileName: task.fileName,
                        fileSize: task.fileSize,
                        localeIdentifier: localeIdentifier
                    )
                }

                if transcription.engine == "whisper_cpp_on_device" {
                    EduMindLog.notice(
                        "OfflineTranscription",
                        "taskId=\(task.taskId) on-device whisper selected effective_model=\(resolvedOnDeviceWhisperModel(localeIdentifier: localeIdentifier, payload: payload))"
                    )
                }

                EduMindLog.info(
                    "OfflineTranscription",
                    "\(offlineProgressBar(100)) taskId=\(task.taskId) phase=completed engine=\(transcription.engine) textLength=\(transcription.text.count) segments=\(transcription.segments.count)"
                )
                sendNativeEvent(name: "offline-transcription-completed", payload: [
                    "taskId": task.taskId,
                    "fileName": task.fileName,
                    "fileSize": task.fileSize,
                    "fileExt": task.fileExt,
                    "status": "completed",
                    "progress": 100,
                    "message": "本地离线转录完成",
                    "locale": transcription.localeIdentifier,
                    "engine": transcription.engine,
                    "transcriptText": transcription.text,
                    "segments": transcription.segments
                ])
            } catch {
                EduMindLog.error("OfflineTranscription", "taskId=\(task.taskId) failed error=\(error.localizedDescription)")
                sendOfflineFailureEvent(
                    taskId: task.taskId,
                    fileName: task.fileName,
                    fileSize: task.fileSize,
                    message: error.localizedDescription,
                    engine: activeEngine
                )
            }

            activeOfflineTasks[task.taskId] = nil
        }

        private func handleNativeBridgeMessage(_ body: [String: Any]) {
            let requestId = String(describing: body["requestId"] ?? "")
            let action = String(describing: body["action"] ?? "")
            let payload = body["payload"] as? [String: Any] ?? [:]

            guard !requestId.isEmpty else {
                EduMindLog.error("Bridge", "received native bridge message without requestId")
                return
            }

            EduMindLog.info("Bridge", "native action=\(action) payload=\(payload)")

            switch action {
            case "ping":
                let formatter = ISO8601DateFormatter()
                respondToNativeRequest(
                    requestId: requestId,
                    success: true,
                    payload: [
                        "platform": "ios",
                        "bridgeVersion": 1,
                        "timestamp": formatter.string(from: Date())
                    ]
                )
            case "getCapabilities":
                respondToNativeRequest(
                    requestId: requestId,
                    success: true,
                    payload: nativeBridgeCapabilities()
                )
            case "startOfflineTranscription":
                startOfflineTranscriptionFlow(requestId: requestId, payload: payload)
            default:
                respondToNativeRequest(
                    requestId: requestId,
                    success: false,
                    errorMessage: "Unsupported native bridge action: \(action)"
                )
            }
        }

        func userContentController(_ userContentController: WKUserContentController, didReceive message: WKScriptMessage) {
            if message.name == Self.logHandlerName {
                if let body = message.body as? [String: Any] {
                    let level = String(describing: body["level"] ?? "log")
                    let payload = String(describing: body["payload"] ?? "")
                    EduMindLog.write(nativeLogLevel(for: level), payload)
                    return
                }
                EduMindLog.notice("Bridge", String(describing: message.body))
                return
            }

            if message.name == Self.pageStateHandlerName {
                handlePageStateMessage(message.body)
                return
            }

            guard message.name == Self.nativeBridgeHandlerName else { return }
            guard let body = message.body as? [String: Any] else {
                EduMindLog.error("Bridge", "received invalid native bridge payload: \(String(describing: message.body))")
                return
            }
            handleNativeBridgeMessage(body)
        }

        func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
            finishLoad()
            EduMindLog.info("WebView", "didFinish navigation: \(webView.url?.absoluteString ?? "<nil>")")
            scheduleBootProbes(for: webView)
        }

        func webView(_ webView: WKWebView, didFail navigation: WKNavigation!, withError error: Error) {
            finishLoad()
            EduMindLog.error("WebView", "didFail navigation: \(error.localizedDescription)")
            showErrorPage(
                in: webView,
                code: .navigationFail,
                title: "页面加载失败",
                details: error.localizedDescription,
                recovery: "请优先检查 Xcode 控制台中的导航错误、WebAssets 是否完整，以及 index.html 是否引用了正确的 index.js/index.css。"
            )
        }

        func webView(_ webView: WKWebView, didFailProvisionalNavigation navigation: WKNavigation!, withError error: Error) {
            finishLoad()
            EduMindLog.error("WebView", "didFailProvisionalNavigation: \(error.localizedDescription)")
            showErrorPage(
                in: webView,
                code: .navigationInitFail,
                title: "页面初始化失败",
                details: error.localizedDescription,
                recovery: "请优先检查本地 index.html 是否存在、read access 路径是否正确，以及前端是否仍输出 iOS 预期的打包布局。"
            )
        }

        private func showErrorPage(
            in webView: WKWebView,
            code: WebViewErrorCode,
            title: String,
            details: String,
            recovery: String
        ) {
            H5WebView.renderErrorPage(
                in: webView,
                code: code,
                title: title,
                details: details,
                recovery: recovery
            )
        }

        func webView(_ webView: WKWebView, start urlSchemeTask: WKURLSchemeTask) {
            guard let requestURL = urlSchemeTask.request.url else {
                urlSchemeTask.didFailWithError(NSError(domain: NSURLErrorDomain, code: NSURLErrorBadURL))
                return
            }

            guard requestURL.host == Self.offlineVideoHost else {
                urlSchemeTask.didFailWithError(NSError(domain: NSURLErrorDomain, code: NSURLErrorUnsupportedURL))
                return
            }

            let taskId = requestURL.path.trimmingCharacters(in: CharacterSet(charactersIn: "/")).removingPercentEncoding ?? ""
            guard let videoURL = resolveOfflineVideoURL(taskId: taskId) else {
                EduMindLog.error("OfflineVideo", "taskId=\(taskId) unresolved request=\(requestURL.absoluteString)")
                urlSchemeTask.didFailWithError(NSError(domain: NSURLErrorDomain, code: NSURLErrorFileDoesNotExist))
                return
            }

            do {
                try respondWithOfflineVideo(
                    requestURL: requestURL,
                    videoURL: videoURL,
                    byteRangeHeader: urlSchemeTask.request.value(forHTTPHeaderField: "Range"),
                    to: urlSchemeTask
                )
            } catch {
                EduMindLog.error("OfflineVideo", "taskId=\(taskId) failed error=\(error.localizedDescription)")
                urlSchemeTask.didFailWithError(error)
            }
        }

        func webView(_ webView: WKWebView, stop urlSchemeTask: WKURLSchemeTask) {
            guard let requestURL = urlSchemeTask.request.url else { return }
            EduMindLog.debug("OfflineVideo", "stop request=\(requestURL.absoluteString)")
        }
    }
}

extension H5WebView.Coordinator: UIDocumentPickerDelegate {
    func documentPickerWasCancelled(_ controller: UIDocumentPickerViewController) {
        guard let requestId = pendingVideoPickerRequestId else { return }
        clearPendingVideoPickerState()
        respondToNativeRequest(
            requestId: requestId,
            success: false,
            errorMessage: NativeOfflineTranscriptionError.pickerCancelled.localizedDescription
        )
    }

    func documentPicker(_ controller: UIDocumentPickerViewController, didPickDocumentsAt urls: [URL]) {
        guard let requestId = pendingVideoPickerRequestId else { return }
        let payload = pendingVideoPickerPayload
        clearPendingVideoPickerState()

        guard let sourceURL = urls.first else {
            respondToNativeRequest(
                requestId: requestId,
                success: false,
                errorMessage: NativeOfflineTranscriptionError.invalidSelection.localizedDescription
            )
            return
        }

        do {
            let task = try buildSelectedVideoMetadata(from: sourceURL)
            persistOfflineVideoURL(taskId: task.taskId, videoURL: task.workingURL)
            respondToNativeRequest(
                requestId: requestId,
                success: true,
                payload: [
                    "taskId": task.taskId,
                    "fileName": task.fileName,
                    "fileSize": task.fileSize,
                    "fileExt": task.fileExt,
                    "status": "preparing",
                    "engine": "apple_speech_on_device",
                    "message": "已选择本地视频，开始本地离线转录"
                ]
            )

            let work = Task { [weak self] in
                guard let self else { return }
                await self.runOfflineTranscription(task: task, payload: payload)
            }
            activeOfflineTasks[task.taskId] = work
        } catch {
            respondToNativeRequest(
                requestId: requestId,
                success: false,
                errorMessage: error.localizedDescription
            )
        }
    }
}

struct ContentView: View {
    var body: some View {
        H5WebView()
            .ignoresSafeArea()
    }
}

struct ContentView_Previews: PreviewProvider {
    static var previews: some View {
        ContentView()
            .previewDisplayName("EduMind iPhone")
            .previewDevice("iPhone 16 Pro")
    }
}
