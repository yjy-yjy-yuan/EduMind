//
//  EduMindIOSApp.swift
//  EduMindIOS
//
//  Created by yuan on 2026/3/12.
//

import Combine
import SwiftUI
import UIKit

private struct UpdateManifest: Decodable {
    let forceUpdate: Bool
    let latestVersion: String?
    let latestBuild: Int?
    let minSupportedBuild: Int?
    let updateURL: String?
    let title: String?
    let message: String?
    let buttonText: String?

    enum CodingKeys: String, CodingKey {
        case forceUpdate = "force_update"
        case latestVersion = "latest_version"
        case latestBuild = "latest_build"
        case minSupportedBuild = "min_supported_build"
        case updateURL = "update_url"
        case title
        case message
        case buttonText = "button_text"
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        forceUpdate = try container.decodeIfPresent(Bool.self, forKey: .forceUpdate) ?? false
        latestVersion = try container.decodeIfPresent(String.self, forKey: .latestVersion)
        latestBuild = Self.decodeInt(from: container, key: .latestBuild)
        minSupportedBuild = Self.decodeInt(from: container, key: .minSupportedBuild)
        updateURL = try container.decodeIfPresent(String.self, forKey: .updateURL)
        title = try container.decodeIfPresent(String.self, forKey: .title)
        message = try container.decodeIfPresent(String.self, forKey: .message)
        buttonText = try container.decodeIfPresent(String.self, forKey: .buttonText)
    }

    private static func decodeInt(from container: KeyedDecodingContainer<CodingKeys>, key: CodingKeys) -> Int? {
        if let value = try? container.decodeIfPresent(Int.self, forKey: key) {
            return value
        }
        if let text = try? container.decode(String.self, forKey: key) {
            return Int(text)
        }
        return nil
    }
}

private struct ForceUpdatePrompt: Identifiable {
    let id = UUID()
    let title: String
    let message: String
    let buttonText: String
    let updateURL: URL
}

@MainActor
private final class ForceUpdateViewModel: ObservableObject {
    @Published var prompt: ForceUpdatePrompt?

    private var didCheck = false

    func checkForForceUpdateIfNeeded() async {
        if didCheck {
            return
        }
        didCheck = true

        guard let manifestURL = manifestURLFromConfig() else {
            return
        }

        do {
            let manifest = try await fetchManifest(from: manifestURL)
            let appBuild = appBuildNumber()
            let appVersion = appVersionString()
            let shouldBlock = shouldForceUpdate(manifest: manifest, appBuild: appBuild, appVersion: appVersion)

            guard shouldBlock, let url = validatedUpdateURL(from: manifest.updateURL) else {
                return
            }

            prompt = ForceUpdatePrompt(
                title: manifest.title ?? "发现新版本",
                message: manifest.message ?? "当前版本已停止支持，请立即更新后继续使用。",
                buttonText: manifest.buttonText ?? "立即更新",
                updateURL: url
            )
        } catch {
            // Ignore network errors to avoid blocking app startup on transient failures.
        }
    }

    func openUpdatePage() {
        guard let url = prompt?.updateURL else {
            return
        }
        UIApplication.shared.open(url)
    }

    private func manifestURLFromConfig() -> URL? {
        guard
            let raw = Bundle.main.object(forInfoDictionaryKey: "EDUMIND_UPDATE_MANIFEST_URL") as? String
        else {
            return nil
        }
        let value = raw.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !value.isEmpty else {
            return nil
        }
        return URL(string: value)
    }

    private func validatedUpdateURL(from raw: String?) -> URL? {
        guard let raw else {
            return nil
        }
        let value = raw.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !value.isEmpty else {
            return nil
        }
        return URL(string: value)
    }

    private func appBuildNumber() -> Int {
        let raw = Bundle.main.object(forInfoDictionaryKey: kCFBundleVersionKey as String) as? String
        return Int(raw ?? "") ?? 0
    }

    private func appVersionString() -> String {
        (Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String) ?? "0.0.0"
    }

    private func shouldForceUpdate(manifest: UpdateManifest, appBuild: Int, appVersion: String) -> Bool {
        let blockedByMinBuild = appBuild < (manifest.minSupportedBuild ?? 0)
        if blockedByMinBuild {
            return true
        }

        let hasNewerBuild = appBuild < (manifest.latestBuild ?? appBuild)
        let hasNewerVersion: Bool
        if let latestVersion = manifest.latestVersion, !latestVersion.isEmpty {
            hasNewerVersion = isVersion(appVersion, lowerThan: latestVersion)
        } else {
            hasNewerVersion = false
        }

        return manifest.forceUpdate && (hasNewerBuild || hasNewerVersion)
    }

    private func fetchManifest(from url: URL) async throws -> UpdateManifest {
        var request = URLRequest(url: url)
        request.timeoutInterval = 6
        request.cachePolicy = .reloadIgnoringLocalAndRemoteCacheData

        let (data, response) = try await URLSession.shared.data(for: request)
        guard let http = response as? HTTPURLResponse, (200 ... 299).contains(http.statusCode) else {
            throw URLError(.badServerResponse)
        }
        return try JSONDecoder().decode(UpdateManifest.self, from: data)
    }

    private func isVersion(_ current: String, lowerThan target: String) -> Bool {
        let lhs = current.split(separator: ".").map { Int($0) ?? 0 }
        let rhs = target.split(separator: ".").map { Int($0) ?? 0 }
        let maxCount = max(lhs.count, rhs.count)

        for index in 0 ..< maxCount {
            let left = index < lhs.count ? lhs[index] : 0
            let right = index < rhs.count ? rhs[index] : 0
            if left < right {
                return true
            }
            if left > right {
                return false
            }
        }
        return false
    }
}

private struct ForceUpdateOverlay: View {
    let prompt: ForceUpdatePrompt
    let onConfirm: () -> Void

    var body: some View {
        ZStack {
            Color.black.opacity(0.48)
                .ignoresSafeArea()

            VStack(alignment: .leading, spacing: 14) {
                Text(prompt.title)
                    .font(.system(size: 21, weight: .bold))
                    .foregroundColor(.primary)
                Text(prompt.message)
                    .font(.system(size: 15))
                    .foregroundColor(.secondary)
                Button(action: onConfirm) {
                    Text(prompt.buttonText)
                        .font(.system(size: 16, weight: .semibold))
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 12)
                }
                .buttonStyle(.borderedProminent)
                .tint(.green)
            }
            .padding(20)
            .background(Color(.systemBackground))
            .cornerRadius(16)
            .padding(24)
            .shadow(color: .black.opacity(0.2), radius: 20, x: 0, y: 12)
        }
    }
}

@main
struct EduMindIOSApp: App {
    @StateObject private var updateViewModel = ForceUpdateViewModel()

    var body: some Scene {
        WindowGroup {
            ZStack {
                ContentView()
                    .disabled(updateViewModel.prompt != nil)

                if let prompt = updateViewModel.prompt {
                    ForceUpdateOverlay(prompt: prompt) {
                        updateViewModel.openUpdatePage()
                    }
                }
            }
            .task {
                await updateViewModel.checkForForceUpdateIfNeeded()
            }
        }
    }
}
