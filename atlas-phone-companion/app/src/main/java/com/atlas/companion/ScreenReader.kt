package com.atlas.companion

import android.graphics.Rect
import android.view.accessibility.AccessibilityNodeInfo

data class ScreenElement(
    val text: String,
    val className: String,
    val bounds: List<Int>,
    val clickable: Boolean
)

object ScreenReader {

    fun walkTree(root: AccessibilityNodeInfo): List<ScreenElement> {
        val result = mutableListOf<ScreenElement>()
        traverse(root, result)
        return result
    }

    private fun traverse(node: AccessibilityNodeInfo?, result: MutableList<ScreenElement>) {
        if (node == null) return

        val text = node.text?.toString() ?: node.contentDescription?.toString() ?: ""
        val bounds = Rect()
        node.getBoundsInScreen(bounds)

        if (text.isNotEmpty() || node.isClickable) {
            result.add(
                ScreenElement(
                    text = text,
                    className = node.className?.toString() ?: "",
                    bounds = listOf(bounds.left, bounds.top, bounds.right, bounds.bottom),
                    clickable = node.isClickable
                )
            )
        }

        for (i in 0 until node.childCount) {
            traverse(node.getChild(i), result)
        }
    }
}
