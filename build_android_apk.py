#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
궁디 플레이어 Ultimate - 안드로이드 네이티브 앱 & 바탕화면 위젯 자동 생성 스크립트
GitHub Actions에서 실행되어 바탕화면 전용 위젯(GungdiWidgetProvider) + 상단바 미디어 서비스 + 칼종료 브릿지가
포함된 정식 안드로이드 프로젝트를 생성합니다.
"""

import os
import shutil
import struct
import zlib

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
ANDROID_DIR = os.path.join(ROOT_DIR, "android-app")


def create_fallback_white_peach_png(target_path, size=192):
    """만약 icon-512.png가 없을 경우에도 빌드가 절대 실패하지 않도록 순백색+피치 원형 PNG를 생성합니다."""
    raw_rows = []
    cx, cy = size / 2.0, size / 2.0
    r_peach = size * 0.28
    for y in range(size):
        row = bytearray([0])  # filter type 0
        for x in range(size):
            dx = x - cx
            dy = y - cy
            if dx * dx + dy * dy <= r_peach * r_peach:
                row.extend((255, 115, 145, 255))
            else:
                row.extend((255, 255, 255, 255))
        raw_rows.append(bytes(row))
    raw_data = b"".join(raw_rows)

    def make_chunk(chunk_type, data):
        chunk = struct.pack(">I", len(data)) + chunk_type + data
        crc = zlib.crc32(chunk_type + data) & 0xFFFFFFFF
        return chunk + struct.pack(">I", crc)

    png = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)
    png += make_chunk(b"IHDR", ihdr)
    png += make_chunk(b"IDAT", zlib.compress(raw_data, 9))
    png += make_chunk(b"IEND", b"")
    with open(target_path, "wb") as f:
        f.write(png)


def write_text(rel_path, content):
    full_path = os.path.join(ANDROID_DIR, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content.lstrip("\n"))


def main():
    if os.path.exists(ANDROID_DIR):
        shutil.rmtree(ANDROID_DIR)
    os.makedirs(ANDROID_DIR, exist_ok=True)

    # 1. settings.gradle
    write_text("settings.gradle", """
pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}
rootProject.name = "GungdiPlayer"
include ':app'
""")

    # 2. build.gradle (root)
    write_text("build.gradle", """
plugins {
    id 'com.android.application' version '8.3.2' apply false
}
""")

    # 3. gradle.properties
    write_text("gradle.properties", """
org.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8
android.useAndroidX=true
android.nonTransitiveRClass=true
""")

    # 4. app/build.gradle
    write_text("app/build.gradle", """
plugins {
    id 'com.android.application'
}

android {
    namespace 'com.gungdi.player'
    compileSdk 34

    defaultConfig {
        applicationId "com.gungdi.player"
        minSdk 24
        targetSdk 34
        versionCode 3
        versionName "3.0-widget"
    }

    signingConfigs {
        release {
            storeFile file("release-key.jks")
            storePassword "gungdi1234"
            keyAlias "gungdi"
            keyPassword "gungdi1234"
        }
    }

    buildTypes {
        debug {
            signingConfig signingConfigs.release
        }
        release {
            minifyEnabled false
            signingConfig signingConfigs.release
        }
    }

    compileOptions {
        sourceCompatibility JavaVersion.VERSION_17
        targetCompatibility JavaVersion.VERSION_17
    }
}

dependencies {
    implementation 'androidx.appcompat:appcompat:1.6.1'
    implementation 'androidx.core:core:1.12.0'
    implementation 'androidx.media:media:1.7.0'
}
""")

    # 5. AndroidManifest.xml
    write_text("app/src/main/AndroidManifest.xml", """
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">

    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.WAKE_LOCK" />
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE" />
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE_MEDIA_PLAYBACK" />
    <uses-permission android:name="android.permission.POST_NOTIFICATIONS" />

    <application
        android:allowBackup="true"
        android:icon="@mipmap/ic_launcher"
        android:roundIcon="@mipmap/ic_launcher"
        android:label="궁디 플레이어"
        android:supportsRtl="true"
        android:usesCleartextTraffic="true"
        android:theme="@style/Theme.AppCompat.NoActionBar">

        <activity
            android:name=".MainActivity"
            android:exported="true"
            android:launchMode="singleTask"
            android:configChanges="orientation|screenSize|keyboardHidden|uiMode">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>

        <service
            android:name=".MediaPlaybackService"
            android:exported="false"
            android:foregroundServiceType="mediaPlayback" />

        <receiver
            android:name=".GungdiWidgetProvider"
            android:exported="true"
            android:label="🍑 궁디 플레이어 위젯">
            <intent-filter>
                <action android:name="android.appwidget.action.APPWIDGET_UPDATE" />
            </intent-filter>
            <meta-data
                android:name="android.appwidget.provider"
                android:resource="@xml/gungdi_widget_info" />
        </receiver>

        <receiver
            android:name=".WidgetActionReceiver"
            android:exported="true">
            <intent-filter>
                <action android:name="com.gungdi.player.ACTION_TOGGLE" />
                <action android:name="com.gungdi.player.ACTION_PREV" />
                <action android:name="com.gungdi.player.ACTION_NEXT" />
                <action android:name="com.gungdi.player.ACTION_STOP" />
            </intent-filter>
        </receiver>

    </application>
</manifest>
""")

    # 6. XML 리소스: 바탕화면 위젯 메타데이터 (res/xml/gungdi_widget_info.xml)
    write_text("app/src/main/res/xml/gungdi_widget_info.xml", """
<?xml version="1.0" encoding="utf-8"?>
<appwidget-provider xmlns:android="http://schemas.android.com/apk/res/android"
    android:minWidth="250dp"
    android:minHeight="64dp"
    android:targetCellWidth="4"
    android:targetCellHeight="1"
    android:updatePeriodMillis="0"
    android:initialLayout="@layout/gungdi_widget"
    android:resizeMode="horizontal|vertical"
    android:widgetCategory="home_screen"
    android:previewImage="@mipmap/ic_launcher" />
""")

    # 7. Drawables for Widget
    write_text("app/src/main/res/drawable/widget_bg.xml", """
<?xml version="1.0" encoding="utf-8"?>
<shape xmlns:android="http://schemas.android.com/apk/res/android"
    android:shape="rectangle">
    <solid android:color="#EE191B22" />
    <corners android:radius="22dp" />
    <stroke android:width="1.5dp" android:color="#55FF477E" />
</shape>
""")

    write_text("app/src/main/res/drawable/widget_play_bg.xml", """
<?xml version="1.0" encoding="utf-8"?>
<shape xmlns:android="http://schemas.android.com/apk/res/android"
    android:shape="oval">
    <solid android:color="#FF477E" />
</shape>
""")

    write_text("app/src/main/res/drawable/widget_art_bg.xml", """
<?xml version="1.0" encoding="utf-8"?>
<shape xmlns:android="http://schemas.android.com/apk/res/android"
    android:shape="rectangle">
    <solid android:color="#FFFFFF" />
    <corners android:radius="14dp" />
</shape>
""")

    # 8. Layout: 바탕화면 위젯 레이아웃 (res/layout/gungdi_widget.xml)
    write_text("app/src/main/res/layout/gungdi_widget.xml", """
<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:id="@+id/widget_root"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:background="@drawable/widget_bg"
    android:gravity="center_vertical"
    android:orientation="horizontal"
    android:paddingLeft="12dp"
    android:paddingRight="10dp"
    android:paddingTop="8dp"
    android:paddingBottom="8dp">

    <ImageView
        android:id="@+id/widget_art"
        android:layout_width="48dp"
        android:layout_height="48dp"
        android:background="@drawable/widget_art_bg"
        android:scaleType="centerCrop"
        android:src="@mipmap/ic_launcher"
        android:contentDescription="앨범 아트" />

    <LinearLayout
        android:id="@+id/widget_info_box"
        android:layout_width="0dp"
        android:layout_height="wrap_content"
        android:layout_weight="1"
        android:layout_marginLeft="11dp"
        android:layout_marginRight="6dp"
        android:orientation="vertical">

        <TextView
            android:id="@+id/widget_badge"
            android:layout_width="wrap_content"
            android:layout_height="wrap_content"
            android:text="🍑 GUNGDI PLAYER"
            android:textColor="#FF6B98"
            android:textSize="9.5sp"
            android:textStyle="bold"
            android:singleLine="true" />

        <TextView
            android:id="@+id/widget_title"
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:layout_marginTop="1dp"
            android:text="궁디 플레이어 터치하여 재생"
            android:textColor="#FFFFFF"
            android:textSize="13.5sp"
            android:textStyle="bold"
            android:singleLine="true"
            android:ellipsize="end" />

        <TextView
            android:id="@+id/widget_artist"
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:layout_marginTop="1dp"
            android:text="궁디 AI Studio"
            android:textColor="#B2B7C2"
            android:textSize="11sp"
            android:singleLine="true"
            android:ellipsize="end" />
    </LinearLayout>

    <LinearLayout
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:gravity="center_vertical"
        android:orientation="horizontal">

        <ImageButton
            android:id="@+id/widget_btn_prev"
            android:layout_width="38dp"
            android:layout_height="38dp"
            android:background="@android:color/transparent"
            android:src="@android:drawable/ic_media_previous"
            android:scaleType="centerInside"
            android:contentDescription="이전 곡" />

        <ImageButton
            android:id="@+id/widget_btn_play"
            android:layout_width="42dp"
            android:layout_height="42dp"
            android:layout_marginLeft="3dp"
            android:layout_marginRight="3dp"
            android:background="@drawable/widget_play_bg"
            android:src="@android:drawable/ic_media_play"
            android:scaleType="centerInside"
            android:contentDescription="재생 및 일시정지" />

        <ImageButton
            android:id="@+id/widget_btn_next"
            android:layout_width="38dp"
            android:layout_height="38dp"
            android:background="@android:color/transparent"
            android:src="@android:drawable/ic_media_next"
            android:scaleType="centerInside"
            android:contentDescription="다음 곡" />
    </LinearLayout>

</LinearLayout>
""")

    # 9. Java: PlaybackStateStore.java (위젯 및 알림 상태 공유 저장소)
    write_text("app/src/main/java/com/gungdi/player/PlaybackStateStore.java", """
package com.gungdi.player;

import android.content.Context;
import android.content.SharedPreferences;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.util.Base64;

public class PlaybackStateStore {
    private static final String PREF_NAME = "gungdi_widget_prefs";
    public static String currentTitle = "궁디 플레이어";
    public static String currentArtist = "궁디 AI Studio";
    public static boolean isPlaying = false;
    public static Bitmap currentArtwork = null;

    public static void save(Context context, String title, String artist, boolean playing, String base64Art) {
        if (title != null && !title.isEmpty()) currentTitle = title;
        if (artist != null && !artist.isEmpty()) currentArtist = artist;
        isPlaying = playing;

        if (base64Art != null && base64Art.startsWith("data:image/")) {
            try {
                int commaIdx = base64Art.indexOf(',');
                if (commaIdx != -1) {
                    String pureBase64 = base64Art.substring(commaIdx + 1);
                    byte[] decoded = Base64.decode(pureBase64, Base64.DEFAULT);
                    Bitmap bmp = BitmapFactory.decodeByteArray(decoded, 0, decoded.length);
                    if (bmp != null) {
                        currentArtwork = bmp;
                    }
                }
            } catch (Exception ignored) {}
        } else if (base64Art != null && base64Art.isEmpty()) {
            currentArtwork = null;
        }

        SharedPreferences prefs = context.getSharedPreferences(PREF_NAME, Context.MODE_PRIVATE);
        prefs.edit()
            .putString("title", currentTitle)
            .putString("artist", currentArtist)
            .putBoolean("isPlaying", isPlaying)
            .apply();
    }

    public static void loadIfNeeded(Context context) {
        if ("궁디 플레이어".equals(currentTitle)) {
            SharedPreferences prefs = context.getSharedPreferences(PREF_NAME, Context.MODE_PRIVATE);
            currentTitle = prefs.getString("title", "궁디 플레이어 터치하여 재생");
            currentArtist = prefs.getString("artist", "궁디 AI Studio");
        }
    }
}
""")

    # 10. Java: GungdiWidgetProvider.java (바탕화면 전용 위젯)
    write_text("app/src/main/java/com/gungdi/player/GungdiWidgetProvider.java", """
package com.gungdi.player;

import android.app.PendingIntent;
import android.appwidget.AppWidgetManager;
import android.appwidget.AppWidgetProvider;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.widget.RemoteViews;

public class GungdiWidgetProvider extends AppWidgetProvider {

    @Override
    public void onUpdate(Context context, AppWidgetManager appWidgetManager, int[] appWidgetIds) {
        PlaybackStateStore.loadIfNeeded(context);
        for (int appWidgetId : appWidgetIds) {
            updateSingleWidget(context, appWidgetManager, appWidgetId);
        }
    }

    public static void updateAllWidgets(Context context) {
        try {
            AppWidgetManager manager = AppWidgetManager.getInstance(context);
            ComponentName component = new ComponentName(context, GungdiWidgetProvider.class);
            int[] ids = manager.getAppWidgetIds(component);
            if (ids != null && ids.length > 0) {
                for (int id : ids) {
                    updateSingleWidget(context, manager, id);
                }
            }
        } catch (Exception ignored) {}
    }

    private static void updateSingleWidget(Context context, AppWidgetManager manager, int appWidgetId) {
        RemoteViews views = new RemoteViews(context.getPackageName(), R.layout.gungdi_widget);

        views.setTextViewText(R.id.widget_title, PlaybackStateStore.currentTitle);
        String subText = PlaybackStateStore.currentArtist + (PlaybackStateStore.isPlaying ? " · 재생 중" : " · 일시정지");
        views.setTextViewText(R.id.widget_artist, subText);

        views.setImageViewResource(
            R.id.widget_btn_play,
            PlaybackStateStore.isPlaying
                ? android.R.drawable.ic_media_pause
                : android.R.drawable.ic_media_play
        );

        if (PlaybackStateStore.currentArtwork != null) {
            views.setImageViewBitmap(R.id.widget_art, PlaybackStateStore.currentArtwork);
        } else {
            views.setImageViewResource(R.id.widget_art, R.mipmap.ic_launcher);
        }

        // 위젯 본체 클릭 시 궁디 플레이어 앱 열기
        Intent openIntent = new Intent(context, MainActivity.class);
        openIntent.addFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP | Intent.FLAG_ACTIVITY_CLEAR_TOP);
        PendingIntent openPending = PendingIntent.getActivity(
            context, 100, openIntent,
            PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
        );
        views.setOnClickPendingIntent(R.id.widget_info_box, openPending);
        views.setOnClickPendingIntent(R.id.widget_art, openPending);

        // 이전곡 / 재생·일시정지 / 다음곡 버튼 연결
        views.setOnClickPendingIntent(R.id.widget_btn_prev, buildActionPendingIntent(context, WidgetActionReceiver.ACTION_PREV, 101));
        views.setOnClickPendingIntent(R.id.widget_btn_play, buildActionPendingIntent(context, WidgetActionReceiver.ACTION_TOGGLE, 102));
        views.setOnClickPendingIntent(R.id.widget_btn_next, buildActionPendingIntent(context, WidgetActionReceiver.ACTION_NEXT, 103));

        manager.updateAppWidget(appWidgetId, views);
    }

    private static PendingIntent buildActionPendingIntent(Context context, String action, int reqCode) {
        Intent intent = new Intent(context, WidgetActionReceiver.class);
        intent.setAction(action);
        return PendingIntent.getBroadcast(
            context, reqCode, intent,
            PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
        );
    }
}
""")

    # 11. Java: WidgetActionReceiver.java (위젯 및 알림창 버튼 이벤트 처리)
    write_text("app/src/main/java/com/gungdi/player/WidgetActionReceiver.java", """
package com.gungdi.player;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;

public class WidgetActionReceiver extends BroadcastReceiver {
    public static final String ACTION_TOGGLE = "com.gungdi.player.ACTION_TOGGLE";
    public static final String ACTION_PREV = "com.gungdi.player.ACTION_PREV";
    public static final String ACTION_NEXT = "com.gungdi.player.ACTION_NEXT";
    public static final String ACTION_STOP = "com.gungdi.player.ACTION_STOP";

    @Override
    public void onReceive(Context context, Intent intent) {
        if (intent == null || intent.getAction() == null) return;
        String action = intent.getAction();

        String cmd = "toggle";
        if (ACTION_PREV.equals(action)) cmd = "prev";
        else if (ACTION_NEXT.equals(action)) cmd = "next";
        else if (ACTION_STOP.equals(action)) cmd = "stop";

        if (MainActivity.instance != null) {
            MainActivity.instance.dispatchWidgetCommandToWeb(cmd);
        } else {
            // 앱이 완전히 꺼져 있을 때 바탕화면 위젯에서 재생을 누른 경우 앱을 깨워 자동 재생
            Intent launch = new Intent(context, MainActivity.class);
            launch.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_SINGLE_TOP);
            launch.putExtra("auto_cmd", cmd);
            context.startActivity(launch);
        }
    }
}
""")

    # 12. Java: MediaPlaybackService.java (상단 알림바 & 잠금화면 미디어 위젯 + 백그라운드 재생 유지 서비스)
    write_text("app/src/main/java/com/gungdi/player/MediaPlaybackService.java", """
package com.gungdi.player;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.content.pm.ServiceInfo;
import android.graphics.BitmapFactory;
import android.os.Build;
import android.os.IBinder;
import android.os.PowerManager;
import android.support.v4.media.MediaMetadataCompat;
import android.support.v4.media.session.MediaSessionCompat;
import android.support.v4.media.session.PlaybackStateCompat;

import androidx.core.app.NotificationCompat;
import androidx.media.app.NotificationCompat.MediaStyle;

public class MediaPlaybackService extends Service {
    private static final String CHANNEL_ID = "gungdi_media_channel";
    private static final int NOTIF_ID = 777;
    private MediaSessionCompat mediaSession;
    private PowerManager.WakeLock wakeLock;

    @Override
    public void onCreate() {
        super.onCreate();
        createChannel();

        PowerManager pm = (PowerManager) getSystemService(Context.POWER_SERVICE);
        if (pm != null) {
            wakeLock = pm.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "GungdiPlayer::AudioWakeLock");
        }

        mediaSession = new MediaSessionCompat(this, "GungdiMediaSession");
        mediaSession.setCallback(new MediaSessionCompat.Callback() {
            @Override
            public void onPlay() {
                if (MainActivity.instance != null) MainActivity.instance.dispatchWidgetCommandToWeb("play");
            }

            @Override
            public void onPause() {
                if (MainActivity.instance != null) MainActivity.instance.dispatchWidgetCommandToWeb("pause");
            }

            @Override
            public void onSkipToNext() {
                if (MainActivity.instance != null) MainActivity.instance.dispatchWidgetCommandToWeb("next");
            }

            @Override
            public void onSkipToPrevious() {
                if (MainActivity.instance != null) MainActivity.instance.dispatchWidgetCommandToWeb("prev");
            }

            @Override
            public void onStop() {
                if (MainActivity.instance != null) MainActivity.instance.dispatchWidgetCommandToWeb("stop");
            }
        });
        mediaSession.setActive(true);
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        if (intent != null && "STOP_SERVICE".equals(intent.getAction())) {
            releaseWakeLock();
            stopForeground(true);
            stopSelf();
            return START_NOT_STICKY;
        }

        if (PlaybackStateStore.isPlaying) {
            acquireWakeLock();
        } else {
            releaseWakeLock();
        }

        Notification notification = buildMediaNotification();
        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                startForeground(NOTIF_ID, notification, ServiceInfo.FOREGROUND_SERVICE_TYPE_MEDIA_PLAYBACK);
            } else {
                startForeground(NOTIF_ID, notification);
            }
        } catch (Exception ignored) {}

        return START_STICKY;
    }

    private Notification buildMediaNotification() {
        long actions = PlaybackStateCompat.ACTION_PLAY
                | PlaybackStateCompat.ACTION_PAUSE
                | PlaybackStateCompat.ACTION_PLAY_PAUSE
                | PlaybackStateCompat.ACTION_SKIP_TO_NEXT
                | PlaybackStateCompat.ACTION_SKIP_TO_PREVIOUS
                | PlaybackStateCompat.ACTION_STOP;

        int state = PlaybackStateStore.isPlaying
                ? PlaybackStateCompat.STATE_PLAYING
                : PlaybackStateCompat.STATE_PAUSED;

        mediaSession.setPlaybackState(new PlaybackStateCompat.Builder()
                .setActions(actions)
                .setState(state, PlaybackStateCompat.PLAYBACK_POSITION_UNKNOWN, 1.0f)
                .build());

        MediaMetadataCompat.Builder metaBuilder = new MediaMetadataCompat.Builder()
                .putString(MediaMetadataCompat.METADATA_KEY_TITLE, PlaybackStateStore.currentTitle)
                .putString(MediaMetadataCompat.METADATA_KEY_ARTIST, PlaybackStateStore.currentArtist);

        if (PlaybackStateStore.currentArtwork != null) {
            metaBuilder.putBitmap(MediaMetadataCompat.METADATA_KEY_ALBUM_ART, PlaybackStateStore.currentArtwork);
        } else {
            metaBuilder.putBitmap(
                MediaMetadataCompat.METADATA_KEY_ALBUM_ART,
                BitmapFactory.decodeResource(getResources(), R.mipmap.ic_launcher)
            );
        }
        mediaSession.setMetadata(metaBuilder.build());

        Intent openIntent = new Intent(this, MainActivity.class);
        openIntent.addFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP | Intent.FLAG_ACTIVITY_CLEAR_TOP);
        PendingIntent contentIntent = PendingIntent.getActivity(
                this, 200, openIntent,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
        );

        PendingIntent prevPending = buildBroadcastPending(WidgetActionReceiver.ACTION_PREV, 201);
        PendingIntent togglePending = buildBroadcastPending(WidgetActionReceiver.ACTION_TOGGLE, 202);
        PendingIntent nextPending = buildBroadcastPending(WidgetActionReceiver.ACTION_NEXT, 203);

        int playPauseIcon = PlaybackStateStore.isPlaying
                ? android.R.drawable.ic_media_pause
                : android.R.drawable.ic_media_play;
        String playPauseLabel = PlaybackStateStore.isPlaying ? "일시정지" : "재생";

        NotificationCompat.Builder builder = new NotificationCompat.Builder(this, CHANNEL_ID)
                .setSmallIcon(R.mipmap.ic_launcher)
                .setContentTitle(PlaybackStateStore.currentTitle)
                .setContentText(PlaybackStateStore.currentArtist)
                .setContentIntent(contentIntent)
                .setVisibility(NotificationCompat.VISIBILITY_PUBLIC)
                .setOngoing(PlaybackStateStore.isPlaying)
                .addAction(android.R.drawable.ic_media_previous, "이전 곡", prevPending)
                .addAction(playPauseIcon, playPauseLabel, togglePending)
                .addAction(android.R.drawable.ic_media_next, "다음 곡", nextPending)
                .setStyle(new MediaStyle()
                        .setMediaSession(mediaSession.getSessionToken())
                        .setShowActionsInCompactView(0, 1, 2));

        if (PlaybackStateStore.currentArtwork != null) {
            builder.setLargeIcon(PlaybackStateStore.currentArtwork);
        } else {
            builder.setLargeIcon(BitmapFactory.decodeResource(getResources(), R.mipmap.ic_launcher));
        }

        return builder.build();
    }

    private PendingIntent buildBroadcastPending(String action, int reqCode) {
        Intent intent = new Intent(this, WidgetActionReceiver.class);
        intent.setAction(action);
        return PendingIntent.getBroadcast(
                this, reqCode, intent,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
        );
    }

    private void createChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationChannel channel = new NotificationChannel(
                    CHANNEL_ID,
                    "궁디 플레이어 재생 컨트롤",
                    NotificationManager.IMPORTANCE_LOW
            );
            channel.setDescription("상단바 및 잠금화면 음악 컨트롤러");
            channel.setShowBadge(false);
            NotificationManager nm = getSystemService(NotificationManager.class);
            if (nm != null) nm.createNotificationChannel(channel);
        }
    }

    private void acquireWakeLock() {
        try {
            if (wakeLock != null && !wakeLock.isHeld()) {
                wakeLock.acquire(6 * 60 * 60 * 1000L);
            }
        } catch (Exception ignored) {}
    }

    private void releaseWakeLock() {
        try {
            if (wakeLock != null && wakeLock.isHeld()) {
                wakeLock.release();
            }
        } catch (Exception ignored) {}
    }

    @Override
    public void onDestroy() {
        releaseWakeLock();
        if (mediaSession != null) {
            mediaSession.setActive(false);
            mediaSession.release();
        }
        super.onDestroy();
    }

    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }
}
""")

    # 13. Java: BackgroundAudioWebView.java (홈 버튼으로 백그라운드 전환 시에도 절대 오디오/타이머가 멈추지 않는 전용 웹뷰)
    write_text("app/src/main/java/com/gungdi/player/BackgroundAudioWebView.java", """
package com.gungdi.player;

import android.content.Context;
import android.view.View;
import android.webkit.WebView;

public class BackgroundAudioWebView extends WebView {
    public BackgroundAudioWebView(Context context) {
        super(context);
    }

    @Override
    protected void onWindowVisibilityChanged(int visibility) {
        // 홈 버튼을 눌러 화면이 내려가도 백그라운드 음악 재생과 다음 곡 자동 재생이 끊기지 않도록 항상 VISIBLE 전달
        super.onWindowVisibilityChanged(View.VISIBLE);
    }
}
""")

    # 14. Java: MainActivity.java (메인 화면 + JS 브릿지 + 칼종료 + 뒤로가기 완벽 제어)
    write_text("app/src/main/java/com/gungdi/player/MainActivity.java", """
package com.gungdi.player;

import android.Manifest;
import android.app.Activity;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.view.View;
import android.view.Window;
import android.webkit.JavascriptInterface;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

import androidx.activity.OnBackPressedCallback;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;

public class MainActivity extends AppCompatActivity {
    public static MainActivity instance;
    private static final String APP_URL = "https://dg1682-commits.github.io/goongdyplay/";
    private static final int FILE_CHOOSER_REQ_CODE = 9001;

    private BackgroundAudioWebView webView;
    private ValueCallback<Uri[]> filePathCallback;
    private String pendingAutoCommand = null;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        instance = this;

        Window window = getWindow();
        if (window != null) {
            window.setStatusBarColor(Color.parseColor("#121318"));
            window.setNavigationBarColor(Color.parseColor("#121318"));
        }

        requestNotificationPermissionIfNeeded();

        if (getIntent() != null && getIntent().hasExtra("auto_cmd")) {
            pendingAutoCommand = getIntent().getStringExtra("auto_cmd");
        }

        webView = new BackgroundAudioWebView(this);
        setContentView(webView);

        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setDatabaseEnabled(true);
        settings.setMediaPlaybackRequiresUserGesture(false);
        settings.setAllowFileAccess(true);
        settings.setAllowContentAccess(true);
        settings.setCacheMode(WebSettings.LOAD_DEFAULT);

        webView.addJavascriptInterface(new AndroidBridge(), "Android");

        webView.setWebViewClient(new WebViewClient() {
            @Override
            public void onPageFinished(WebView view, String url) {
                super.onPageFinished(view, url);
                if (pendingAutoCommand != null) {
                    final String cmd = pendingAutoCommand;
                    pendingAutoCommand = null;
                    webView.postDelayed(() -> dispatchWidgetCommandToWeb(cmd), 600);
                }
            }
        });

        webView.setWebChromeClient(new WebChromeClient() {
            @Override
            public boolean onShowFileChooser(WebView webView, ValueCallback<Uri[]> filePathCallback, FileChooserParams fileChooserParams) {
                if (MainActivity.this.filePathCallback != null) {
                    MainActivity.this.filePathCallback.onReceiveValue(null);
                }
                MainActivity.this.filePathCallback = filePathCallback;
                try {
                    Intent intent = new Intent(Intent.ACTION_GET_CONTENT);
                    intent.addCategory(Intent.CATEGORY_OPENABLE);
                    intent.setType("audio/*");
                    intent.putExtra(Intent.EXTRA_ALLOW_MULTIPLE, true);
                    startActivityForResult(Intent.createChooser(intent, "오디오 파일 선택"), FILE_CHOOSER_REQ_CODE);
                    return true;
                } catch (Exception e) {
                    MainActivity.this.filePathCallback = null;
                    return false;
                }
            }
        });

        // 안드로이드 하드웨어 뒤로가기 버튼을 웹앱의 handleAndroidBackKey()로 100% 직결!
        getOnBackPressedDispatcher().addCallback(this, new OnBackPressedCallback(true) {
            @Override
            public void handleOnBackPressed() {
                if (webView != null) {
                    webView.evaluateJavascript(
                        "if (window.handleAndroidBackKey) { window.handleAndroidBackKey(); } else { navigateBack(true); }",
                        null
                    );
                }
            }
        });

        webView.loadUrl(APP_URL);
        GungdiWidgetProvider.updateAllWidgets(this);
    }

    @Override
    protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        setIntent(intent);
        if (intent != null && intent.hasExtra("auto_cmd")) {
            String cmd = intent.getStringExtra("auto_cmd");
            if (cmd != null) {
                dispatchWidgetCommandToWeb(cmd);
            }
        }
    }

    public void dispatchWidgetCommandToWeb(final String cmd) {
        runOnUiThread(() -> {
            if (webView != null) {
                webView.evaluateJavascript(
                    "if (window.handleAndroidWidgetCommand) { window.handleAndroidWidgetCommand('" + cmd + "'); }",
                    null
                );
            }
        });
    }

    private void requestNotificationPermissionIfNeeded() {
        if (Build.VERSION.SDK_INT >= 33) {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS)
                    != PackageManager.PERMISSION_GRANTED) {
                ActivityCompat.requestPermissions(
                        this,
                        new String[]{Manifest.permission.POST_NOTIFICATIONS},
                        1001
                );
            }
        }
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == FILE_CHOOSER_REQ_CODE) {
            if (filePathCallback == null) return;
            Uri[] results = null;
            if (resultCode == Activity.RESULT_OK && data != null) {
                if (data.getClipData() != null) {
                    int count = data.getClipData().getItemCount();
                    results = new Uri[count];
                    for (int i = 0; i < count; i++) {
                        results[i] = data.getClipData().getItemAt(i).getUri();
                    }
                } else if (data.getData() != null) {
                    results = new Uri[]{data.getData()};
                }
            }
            filePathCallback.onReceiveValue(results);
            filePathCallback = null;
        }
    }

    public class AndroidBridge {
        @JavascriptInterface
        public void updatePlaybackState(String title, String artist, boolean isPlaying, String base64Art) {
            PlaybackStateStore.save(MainActivity.this, title, artist, isPlaying, base64Art);
            GungdiWidgetProvider.updateAllWidgets(MainActivity.this);

            Intent serviceIntent = new Intent(MainActivity.this, MediaPlaybackService.class);
            try {
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                    startForegroundService(serviceIntent);
                } else {
                    startService(serviceIntent);
                }
            } catch (Exception ignored) {}
        }

        @JavascriptInterface
        public void stopPlaybackService() {
            PlaybackStateStore.save(MainActivity.this, PlaybackStateStore.currentTitle, PlaybackStateStore.currentArtist, false, "");
            GungdiWidgetProvider.updateAllWidgets(MainActivity.this);
            Intent stopIntent = new Intent(MainActivity.this, MediaPlaybackService.class);
            stopIntent.setAction("STOP_SERVICE");
            try {
                startService(stopIntent);
            } catch (Exception ignored) {}
        }

        @JavascriptInterface
        public void closeApp() {
            runOnUiThread(() -> {
                try {
                    PlaybackStateStore.save(MainActivity.this, PlaybackStateStore.currentTitle, PlaybackStateStore.currentArtist, false, "");
                    GungdiWidgetProvider.updateAllWidgets(MainActivity.this);
                    Intent stopIntent = new Intent(MainActivity.this, MediaPlaybackService.class);
                    stopIntent.setAction("STOP_SERVICE");
                    stopService(stopIntent);
                } catch (Exception ignored) {}

                try {
                    if (webView != null) {
                        webView.loadUrl("about:blank");
                        webView.destroy();
                        webView = null;
                    }
                } catch (Exception ignored) {}

                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
                    finishAndRemoveTask();
                } else {
                    finish();
                }
                System.exit(0);
            });
        }

        @JavascriptInterface
        public void exitApp() {
            closeApp();
        }
    }

    @Override
    protected void onDestroy() {
        if (instance == this) instance = null;
        super.onDestroy();
    }
}
""")

    # 15. 앱 아이콘 복사 (icon-512.png 또는 icon-192.png가 있으면 그대로 사용, 없으면 깔끔한 흰색+복숭아 PNG 생성)
    mipmap_dirs = [
        "app/src/main/res/mipmap-mdpi",
        "app/src/main/res/mipmap-hdpi",
        "app/src/main/res/mipmap-xhdpi",
        "app/src/main/res/mipmap-xxhdpi",
        "app/src/main/res/mipmap-xxxhdpi",
    ]
    icon_src = None
    for candidate in ["icon-512.png", "icon-192.png"]:
        p = os.path.join(ROOT_DIR, candidate)
        if os.path.exists(p):
            icon_src = p
            break

    for d in mipmap_dirs:
        full_d = os.path.join(ANDROID_DIR, d)
        os.makedirs(full_d, exist_ok=True)
        target_png = os.path.join(full_d, "ic_launcher.png")
        if icon_src:
            shutil.copyfile(icon_src, target_png)
        else:
            create_fallback_white_peach_png(target_png, 192)

    print("Android native project with Home Screen Widget generated successfully at:", ANDROID_DIR)


if __name__ == "__main__":
    main()
