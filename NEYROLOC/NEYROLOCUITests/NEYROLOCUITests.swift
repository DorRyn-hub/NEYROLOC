//
//  NEYROLOCUITests.swift
//  NEYROLOCUITests
//
//  Created by RDev9 on 24.07.2026.
//

import XCTest

final class NEYROLOCUITests: XCTestCase {

    override func setUpWithError() throws {
        // Put setup code here. This method is called before the invocation of each test method in the class.

        // In UI tests it is usually best to stop immediately when a failure occurs.
        continueAfterFailure = false

        // In UI tests it’s important to set the initial state - such as interface orientation - required for your tests before they run. The setUp method is a good place to do this.
    }

    override func tearDownWithError() throws {
        // Put teardown code here. This method is called after the invocation of each test method in the class.
    }

    @MainActor
    func testAuroraWelcomeAndManualSetup() throws {
        let app = XCUIApplication()
        app.launchArguments = ["-resetServer"]
        app.launch()

        XCTAssertTrue(app.otherElements["auroraWelcome"].waitForExistence(timeout: 5))
        XCTAssertTrue(app.buttons["scanQRCodeButton"].exists)
        XCTAssertTrue(app.staticTexts["ЛОКАЛЬНО + ОБЛАКО"].exists)
        XCTAssertTrue(app.staticTexts["ПРИВАТНО"].exists)
        XCTAssertTrue(app.staticTexts["Поток"].exists)
        XCTAssertFalse(app.staticTexts["AURORA WORKSPACE"].exists)

        app.buttons["manualAddressButton"].tap()
        XCTAssertTrue(app.textFields["serverAddressField"].waitForExistence(timeout: 3))
        XCTAssertTrue(app.buttons["connectButton"].exists)
    }

    @MainActor
    func testLaunchPerformance() throws {
        // This measures how long it takes to launch your application.
        measure(metrics: [XCTApplicationLaunchMetric()]) {
            let app = XCUIApplication()
            app.launchArguments = ["-resetServer"]
            app.launch()
        }
    }
}
