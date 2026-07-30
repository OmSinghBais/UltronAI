package com.atlas.companion

import android.util.Log
import org.java_websocket.WebSocket
import org.java_websocket.handshake.ClientHandshake
import org.java_websocket.server.WebSocketServer
import org.json.JSONArray
import org.json.JSONObject
import java.net.InetSocketAddress

class CompanionWebSocketServer(
    port: Int,
    private val service: AccessibilityControlService
) : WebSocketServer(InetSocketAddress(port)) {

    companion object {
        private const val TAG = "AtlasWSServer"
    }

    override fun onOpen(conn: WebSocket, handshake: ClientHandshake) {
        Log.i(TAG, "Client connected: ${conn.remoteSocketAddress}")
    }

    override fun onClose(conn: WebSocket, code: Int, reason: String, remote: Boolean) {
        Log.i(TAG, "Client disconnected: ${conn?.remoteSocketAddress}")
    }

    override fun onMessage(conn: WebSocket, message: String) {
        try {
            val json = JSONObject(message)
            val action = json.optString("action")
            val response = JSONObject()

            when (action) {
                "tap" -> {
                    val x = json.getInt("x")
                    val y = json.getInt("y")
                    val ok = service.performTap(x, y)
                    response.put("status", if (ok) "ok" else "error")
                    response.put("action", "tap")
                }
                "type" -> {
                    val text = json.getString("text")
                    val ok = service.performTypeText(text)
                    response.put("status", if (ok) "ok" else "error")
                    response.put("action", "type")
                }
                "open_app" -> {
                    val pkg = json.getString("package")
                    val ok = service.openApp(pkg)
                    response.put("status", if (ok) "ok" else "error")
                    response.put("action", "open_app")
                }
                "read_screen" -> {
                    val elements = service.readScreen()
                    val arr = JSONArray()
                    for (el in elements) {
                        val item = JSONObject()
                        item.put("text", el.text)
                        item.put("class", el.className)
                        item.put("bounds", JSONArray(el.bounds))
                        item.put("clickable", el.clickable)
                        arr.put(item)
                    }
                    response.put("status", "ok")
                    response.put("elements", arr)
                }
                else -> {
                    response.put("status", "error")
                    response.put("reason", "Unknown action '$action'")
                }
            }

            conn.send(response.toString())
        } catch (e: Exception) {
            Log.e(TAG, "Error handling message: ${e.message}", e)
            val errRes = JSONObject()
            errRes.put("status", "error")
            errRes.put("reason", e.message ?: "Server error")
            conn.send(errRes.toString())
        }
    }

    override fun onError(conn: WebSocket?, ex: Exception) {
        Log.e(TAG, "WebSocket error: ${ex.message}", ex)
    }

    override fun onStart() {
        Log.i(TAG, "WebSocket server started successfully.")
    }
}
