package com.atlas.companion

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.GestureDescription
import android.content.Intent
import android.graphics.Path
import android.graphics.Rect
import android.os.Bundle
import android.util.Log
import android.view.accessibility.AccessibilityEvent
import android.view.accessibility.AccessibilityNodeInfo
import org.json.JSONArray
import org.json.JSONObject

class AccessibilityControlService : AccessibilityService() {

    companion object {
        private const val TAG = "AtlasAccessibilitySvc"
        @Volatile
        var instance: AccessibilityControlService? = null
    }

    private var wsServer: CompanionWebSocketServer? = null

    override fun onServiceConnected() {
        super.onServiceConnected()
        instance = this
        Log.i(TAG, "Accessibility Service Connected")
        startWebSocketServer()
    }

    private fun startWebSocketServer() {
        try {
            if (wsServer == null) {
                wsServer = CompanionWebSocketServer(8765)
                wsServer?.isReuseAddr = true
                wsServer?.start()
                Log.i(TAG, "Companion WebSocket server started on port 8765")
            }
        } catch (e: Exception) {
            Log.e(TAG, "Failed to start WebSocket server", e)
        }
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {
        // Event listener for screen state updates
    }

    override fun onInterrupt() {
        Log.w(TAG, "Accessibility Service Interrupted")
    }

    override fun onDestroy() {
        super.onDestroy()
        instance = null
        try {
            wsServer?.stop()
            wsServer = null
        } catch (e: Exception) {
            Log.e(TAG, "Error stopping WebSocket server", e)
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
        val focusedNode = root.findFocus(AccessibilityNodeInfo.FOCUS_INPUT)
            ?: findFirstEditableNode(root)
            ?: return false

        val arguments = Bundle().apply {
            putCharSequence(AccessibilityNodeInfo.ACTION_ARGUMENT_SET_TEXT_CHARSEQUENCE, text)
        }
        return focusedNode.performAction(AccessibilityNodeInfo.ACTION_SET_TEXT, arguments)
    }

    private fun findFirstEditableNode(node: AccessibilityNodeInfo?): AccessibilityNodeInfo? {
        if (node == null) return null
        if (node.isEditable) return node
        for (i in 0 until node.childCount) {
            val child = node.getChild(i)
            val result = findFirstEditableNode(child)
            if (result != null) return result
        }
        return null
    }

    fun openApp(packageName: String): Boolean {
        val launchIntent = packageManager.getLaunchIntentForPackage(packageName) ?: return false
        launchIntent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        startActivity(launchIntent)
        return true
    }

    fun readScreenTree(): JSONArray {
        val elementsArray = JSONArray()
        val root = rootInActiveWindow ?: return elementsArray
        walkNodeTree(root, elementsArray)
        return elementsArray
    }

    private fun walkNodeTree(node: AccessibilityNodeInfo?, result: JSONArray) {
        if (node == null) return

        val text = node.text?.toString() ?: node.contentDescription?.toString()
        if (!text.isNullOrEmpty()) {
            val bounds = Rect()
            node.getBoundsInScreen(bounds)
            val elementJson = JSONObject().apply {
                put("text", text)
                val boundsArray = JSONArray().apply {
                    put(bounds.left)
                    put(bounds.top)
                    put(bounds.right)
                    put(bounds.bottom)
                }
                put("bounds", boundsArray)
                if (node.viewIdResourceName != null) {
                    put("id", node.viewIdResourceName)
                }
            }
            result.put(elementJson)
        }

        for (i in 0 until node.childCount) {
            val child = node.getChild(i)
            walkNodeTree(child, result)
        }
    }
}
