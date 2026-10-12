package com.happyfamily.baselinego;

import android.app.Activity;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.widget.Toast;

/** Launcher shortcut: opens https://www.baselinego.com in the phone's default browser (Chrome, Samsung Internet...) and exits. */
public class MainActivity extends Activity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        Intent intent = new Intent(Intent.ACTION_VIEW, Uri.parse(getString(R.string.start_url)));
        intent.addCategory(Intent.CATEGORY_BROWSABLE);
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        try {
            startActivity(intent);
        } catch (ActivityNotFoundException e) {
            Toast.makeText(this, "브라우저 앱을 찾을 수 없습니다", Toast.LENGTH_LONG).show();
        }
        finish();
    }
}
