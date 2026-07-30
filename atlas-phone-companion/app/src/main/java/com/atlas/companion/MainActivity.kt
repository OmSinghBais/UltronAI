package com.atlas.companion

import android.content.Intent
import android.os.Bundle
import android.provider.Settings
import android.widget.Button
import android.widget.LinearLayout
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity

class MainActivity : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val layout = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(48, 48, 48, 48)
        }

        val titleView = TextView(this).apply {
            text = "ATLAS Phone Companion"
            textSize = 24f
            setPadding(0, 0, 0, 32)
        }

        val statusView = TextView(this).apply {
            text = "Grant Accessibility permission to enable the ATLAS voice control bridge over WebSocket."
            textSize = 16f
            setPadding(0, 0, 0, 32)
        }

        val grantBtn = Button(this).apply {
            text = "Open Accessibility Settings"
            setOnClickListener {
                startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS))
            }
        }

        layout.addView(titleView)
        layout.addView(statusView)
        layout.addView(grantBtn)

        setContentView(layout)
    }
}
