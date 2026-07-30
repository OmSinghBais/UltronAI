package com.atlas.companion

import android.util.Log
import org.java_websocket.WebSocket
import org.java_websocket.handshake.ClientHandshake
import org.java_websocket.server.WebSocketServer
import org.json.JSONObject
import java.net.InetSocketAddress

class CompanionWebSocketServer(port: Int = 8765) : WebSocketServer(InetSocketAddress(port)) {

    companion object {
        private const val TAG = "CompanionWSServer"
    }

    override fun onOpen(conn: WebSocket?, handshake: ClientHandshake?) {
        Log.i(TAG, "Client connected: ${conn?.remoteSocketAddress}")
    }

    override fun onClose(conn: WebSocket?, code: Int, reason: String?, remote: Boolean) {
        Log.i(TAG, "Client disconnected: $reason")
    }

    override fun onMessage(conn: WebSocket?, message: String?) {
        Log.i(TAG, "Received message: $message")
        if (message == null || conn == null) return

        try {
            val json = JSONObject(message)
            val action = json.optString("action")
            val service = AccessibilityControlService.instance

            if (service == null) {
                val errResp = JSONObject().apply {
                    put("status", "error")
                    put("reason", "AccessibilityService is not active")
                }
                conn.send(errResp.toString())
                return
            }

            when (action) {
                "tap" -> {
                    val x = json.getInt("x")
                    val y = json.getInt("y")
                    val success = service.performTap(x, y)
                    val resp = JSONObject().apply {
                        put("status", if (success) "ok" else "error")
                        put("action", "tap")
                        if (!success) put("reason", "Gesture dispatch failed")
                    }
                    conn.send(resp.toString())
                }
                "type" -> {
                    val text = json.getString("text")
                    val success = service.performTypeText(text)
                    val resp = JSONObject().apply {
                        put("status", if (success) "ok" else "error")
                        put("action", "type")
                        if (!success) put("reason", "No focused editable element found")
                    }
                    conn.send(resp.toString())
                }
                "open_app" -> {
                    val packageName = json.getString("package")
                    val success = service.openApp(packageName)
                    val resp = JSONObject().apply {
                        put("status", if (success) "ok" else "error")
                        put("action", "open_app")
                        if (!success) put("reason", "App package not found or launch failed")
                    }
                    conn.send(resp.toString())
                }
                "read_screen" -> {
                    val elements = service.readScreenTree()
                    val resp = JSONObject().apply {
                        put("status", "ok")
                        put("elements", elements)
                    }
                    conn.send(resp.toString())
                }
                else -> {
                    val resp = JSONObject().apply {
                        put("status", "error")
                        put("reason", "Unknown action: $action")
                    }
                    conn.send(resp.toString())
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error handling message", e)
            val errResp = JSONObject().apply {
                put("status", "error")
                put("reason", e.message ?: "Invalid JSON payload")
            }
            conn.send(errResp.toString())
        }
    }

    override fun onError(conn: WebSocket?, ex: Exception?) {
        Log.e(TAG, "WebSocket server error", ex)
    }

    override fun onStart() {
        Log.i(TAG, "WebSocket server started on port $port")
    }
}
