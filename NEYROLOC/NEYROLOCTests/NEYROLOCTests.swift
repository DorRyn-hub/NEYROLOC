//
//  NEYROLOCTests.swift
//  NEYROLOCTests
//
//  Created by RDev9 on 24.07.2026.
//

import Foundation
import Testing
@testable import NEYROLOC

struct NEYROLOCTests {

    @Test func serverAddressNormalization() {
        #expect(ServerAddress.normalize("192.168.1.5") == "http://192.168.1.5:8765")
        #expect(ServerAddress.normalize("neyroloc.local") == "http://neyroloc.local:8765")
        #expect(ServerAddress.normalize("example.test") == "https://example.test")
        #expect(ServerAddress.normalize("https://example.test/path") == "https://example.test/path")
        #expect(ServerAddress.validatedURL("ftp://example.test") == nil)
        #expect(ServerAddress.validatedURL("https://user:pass@example.test") == nil)
        #expect(ServerAddress.validatedURL("http://example.test") == nil)
        #expect(ServerAddress.validatedURL("http://fcevil.example") == nil)
        #expect(ServerAddress.validatedURL("http://fdomain.example") == nil)
        #expect(ServerAddress.validatedURL("http://192.168.1.5:8765") != nil)
        #expect(ServerAddress.validatedURL("http://100.96.10.4:8765") != nil)
        #expect(ServerAddress.validatedURL("http://neyroloc.local:8765") != nil)
        #expect(ServerAddress.validatedURL("https://example.test") != nil)
        #expect(ServerAddress.validatedURL("https://device.example.test:7443/#code=123456") != nil)
        #expect(ServerAddress.validatedURL("http://192.168.1.5:8765/#code=123456") != nil)
        #expect(ServerAddress.validatedURL("http://192.168.1.5:8765/#code=12345") == nil)
        #expect(ServerAddress.validatedURL("http://192.168.1.5:8765/#other=123456") == nil)
    }

    @Test func sameOriginIncludesSchemeHostAndEffectivePort() throws {
        let base = try #require(URL(string: "https://example.test/chat?code=123456"))
        let asset = try #require(URL(string: "https://example.test/mark.svg"))
        let foreign = try #require(URL(string: "https://other.example.test/"))
        let downgraded = try #require(URL(string: "http://example.test/"))

        #expect(ServerAddress.sameOrigin(base, asset))
        #expect(!ServerAddress.sameOrigin(base, foreign))
        #expect(!ServerAddress.sameOrigin(base, downgraded))
    }

}
