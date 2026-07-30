package com.atlas.companion

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.GestureDescription
import android.content.Intent
import android.graphics.Path
import android.os.Bundle
import android.util.Log
import android.view.accessibility.AccessibilityEvent
import android.view.accessibility.AccessibilityNodeInfo

class AccessibilityControlService : AccessibilityService() {

    companion object {
        var instance: AccessibilityControlService? = null
            private set
        private const val TAG = "AtlasAccessibility"
        private const val WS_PORT = 8765
    }

    private var server: CompanionWebSocketServer? = null

    override fun onServiceConnected() {
        super.onServiceConnected()
        instance = this
        Log.i(TAG, "AccessibilityControlService connected.")
        startWebSocketServer()
    }

    private fun startWebSocketServer() {
        try {
            if (server == null) {
                server = CompanionWebSocketServer(WS_PORT, this)
                server?.start()
                Log.i(TAG, "WebSocket server started on port $WS_PORT")
            }
        } catch (e: Exception) {
            Log.e(TAG, "Failed to start WebSocket server: ${e.message}", e)
        }
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {}

    override fun onInterrupt() {
        Log.w(TAG, "AccessibilityService interrupted.")
    }

    override fun onDestroy() {
        super.onDestroy()
        instance = null
        try {
            server?.stop()
        } catch (e: Exception) {
            Log.e(TAG, "Error stopping server", e)
        }
    }

    fun performTap(x: Int, y: Int): Boolean {
        val path = Path().apply { moveTo(x.toFloat(), y.toFloat()) }
        val stroke = GestureDescription.StrokeDescription(path, 0, 50)
        val gesture = GestureDescription.Builder().addStroke(stroke).build()
        return dispatchGesture(gesture, null, null)
    }

    fun performTypeText(text: String): Boolean {
        val root = rootInActiveWindow ?: return false
        val focused = root.findFocus(AccessibilityNodeInfo.FOCUS_INPUT) ?: return false
        val args = Bundle().apply {
            putCharSequence(AccessibilityNodeInfo.ACTION_ARGUMENT_SET_TEXT_CHARSEQUENCE, text)
        }
        return focused.performAction(AccessibilityNodeInfo.ACTION_SET_TEXT, args)
    }

    fun openApp(packageName: String): Boolean {
        return try {
            val launchIntent = packageManager.getLaunchIntentForPackage(packageName)
            if (launchIntent != null) {
                launchIntent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                startActivity(launchIntent)
                true
            } else {
                false
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error opening app $packageName: ${e.message}")
            false
        }
    }

    fun readScreen(): List<ScreenElement> {
        val root = rootInActiveWindow ?: return emptyList()
        return ScreenReader.walkTree(root)
    }
}
