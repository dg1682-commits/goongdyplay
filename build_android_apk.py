#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
궁디 플레이어 Ultimate - 안드로이드 네이티브 앱 & 아이유 스타일 앨범 카드 위젯 + 슬림 위젯 생성 스크립트
- 외부 라이브러리 충돌 없는 100% Pure Android SDK
- 위젯 2종 제공:
  1) 🍑 궁디 앨범 카드 위젯 (아이유 '라일락' 위젯 스타일 · 3x3 기본 / 크기 조절 가능)
  2) 🍑 궁디 슬림 바 위젯 (가로 바 스타일 · 4x1 기본 / 크기 조절 가능)
- 화이트 모드 / 다크 모드 + 투명도(15%~100%) 실시간 반영 + 위젯 우측 상단 ⚙ 설정 바로가기 버튼
- 상단 알림바 & 잠금화면 위젯 진행 상태바(프로그레스바) 실시간 작동 및 구간 탐색(Seek) 연동
"""

import os
import shutil
import struct
import zlib

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
ANDROID_DIR = os.path.join(ROOT_DIR, "android-app")


def create_fallback_white_peach_png(target_path, size=192):
    raw_rows = []
    cx, cy = size / 2.0, size / 2.0
    r_peach = size * 0.28
    for y in range(size):
        row = bytearray([0])
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
        minSdk 26
        targetSdk 34
        versionCode 5
        versionName "5.0-iu-widget"
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

    lint {
        checkReleaseBuilds false
        abortOnError false
    }

    compileOptions {
        sourceCompatibility JavaVersion.VERSION_17
        targetCompatibility JavaVersion.VERSION_17
    }
}

dependencies {
}
""")

    # 5. AndroidManifest.xml (앨범 카드형 3x3 위젯 + 슬림 가로형 4x1 위젯 2종 모두 등록!)
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
        android:theme="@android:style/Theme.DeviceDefault.NoActionBar">

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

        <!-- 위젯 1: 아이유 '라일락' 스타일 앨범 카드형 위젯 (3x3 / 크기 자유 조절) -->
        <receiver
            android:name=".GungdiWidgetProvider"
            android:exported="true"
            android:label="🍑 궁디 앨범 카드 위젯 (3x3)">
            <intent-filter>
                <action android:name="android.appwidget.action.APPWIDGET_UPDATE" />
            </intent-filter>
            <meta-data
                android:name="android.appwidget.provider"
                android:resource="@xml/gungdi_card_widget_info" />
        </receiver>

        <!-- 위젯 2: 슬림 가로형 미니 위젯 (4x1 / 크기 자유 조절) -->
        <receiver
            android:name=".GungdiMiniWidgetProvider"
            android:exported="true"
            android:label="🍑 궁디 슬림 바 위젯 (4x1)">
            <intent-filter>
                <action android:name="android.appwidget.action.APPWIDGET_UPDATE" />
            </intent-filter>
            <meta-data
                android:name="android.appwidget.provider"
                android:resource="@xml/gungdi_mini_widget_info" />
        </receiver>

        <receiver
            android:name=".WidgetActionReceiver"
            android:exported="true">
            <intent-filter>
                <action android:name="com.gungdi.player.ACTION_TOGGLE" />
                <action android:name="com.gungdi.player.ACTION_PREV" />
                <action android:name="com.gungdi.player.ACTION_NEXT" />
                <action android:name="com.gungdi.player.ACTION_STOP" />
                <action android:name="com.gungdi.player.ACTION_OPEN_SETTINGS" />
            </intent-filter>
        </receiver>

    </application>
</manifest>
""")

    # 6. XML 리소스: 카드형 위젯 정보 (3x3 기본, 2x2 ~ 5x5 리사이즈 가능)
    write_text("app/src/main/res/xml/gungdi_card_widget_info.xml", """
<?xml version="1.0" encoding="utf-8"?>
<appwidget-provider xmlns:android="http://schemas.android.com/apk/res/android"
    android:minWidth="180dp"
    android:minHeight="180dp"
    android:minResizeWidth="140dp"
    android:minResizeHeight="140dp"
    android:targetCellWidth="3"
    android:targetCellHeight="3"
    android:updatePeriodMillis="0"
    android:initialLayout="@layout/gungdi_card_widget"
    android:resizeMode="horizontal|vertical"
    android:widgetCategory="home_screen"
    android:previewImage="@mipmap/ic_launcher" />
""")

    # 7. XML 리소스: 슬림 바 위젯 정보 (4x1 기본, 자유 리사이즈 가능)
    write_text("app/src/main/res/xml/gungdi_mini_widget_info.xml", """
<?xml version="1.0" encoding="utf-8"?>
<appwidget-provider xmlns:android="http://schemas.android.com/apk/res/android"
    android:minWidth="250dp"
    android:minHeight="64dp"
    android:minResizeWidth="180dp"
    android:minResizeHeight="56dp"
    android:targetCellWidth="4"
    android:targetCellHeight="1"
    android:updatePeriodMillis="0"
    android:initialLayout="@layout/gungdi_mini_widget"
    android:resizeMode="horizontal|vertical"
    android:widgetCategory="home_screen"
    android:previewImage="@mipmap/ic_launcher" />
""")

    # 8. Layout 1: 아이유 스타일 앨범 카드 위젯 레이아웃 (Canvas 렌더링 이미지 + 투명 터치 영역 오버레이)
    write_text("app/src/main/res/layout/gungdi_card_widget.xml", """
<?xml version="1.0" encoding="utf-8"?>
<FrameLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:id="@+id/card_widget_root"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:padding="4dp">

    <!-- 고해상도 캔버스로 그려지는 라운드 앨범아트 + 하단 플로팅 바 이미지 -->
    <ImageView
        android:id="@+id/card_canvas_img"
        android:layout_width="match_parent"
        android:layout_height="match_parent"
        android:scaleType="fitXY"
        android:contentDescription="궁디 플레이어 앨범 카드 위젯" />

    <!-- 상단 영역: 좌측/중앙 클릭 시 앱 열기, 우측 상단 클릭 시 위젯 설정 바로 열기 -->
    <LinearLayout
        android:layout_width="match_parent"
        android:layout_height="match_parent"
        android:orientation="vertical">

        <LinearLayout
            android:layout_width="match_parent"
            android:layout_height="0dp"
            android:layout_weight="62"
            android:orientation="horizontal">

            <FrameLayout
                android:id="@+id/card_hit_open_top"
                android:layout_width="0dp"
                android:layout_height="match_parent"
                android:layout_weight="1" />

            <FrameLayout
                android:id="@+id/card_hit_settings"
                android:layout_width="54dp"
                android:layout_height="54dp" />
        </LinearLayout>

        <!-- 하단 플로팅 바 터치 영역 (좌측 곡정보=앱열기 / 우측 이전·재생·다음 버튼) -->
        <LinearLayout
            android:layout_width="match_parent"
            android:layout_height="0dp"
            android:layout_weight="38"
            android:orientation="horizontal"
            android:paddingLeft="14dp"
            android:paddingRight="14dp"
            android:paddingBottom="8dp">

            <FrameLayout
                android:id="@+id/card_hit_open_info"
                android:layout_width="0dp"
                android:layout_height="match_parent"
                android:layout_weight="46" />

            <FrameLayout
                android:id="@+id/card_hit_prev"
                android:layout_width="0dp"
                android:layout_height="match_parent"
                android:layout_weight="17" />

            <FrameLayout
                android:id="@+id/card_hit_play"
                android:layout_width="0dp"
                android:layout_height="match_parent"
                android:layout_weight="20" />

            <FrameLayout
                android:id="@+id/card_hit_next"
                android:layout_width="0dp"
                android:layout_height="match_parent"
                android:layout_weight="17" />
        </LinearLayout>
    </LinearLayout>
</FrameLayout>
""")

    # 9. Layout 2: 슬림 바 위젯 레이아웃 (4x1 가로형)
    write_text("app/src/main/res/layout/gungdi_mini_widget.xml", """
<?xml version="1.0" encoding="utf-8"?>
<FrameLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:id="@+id/mini_widget_root"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:padding="2dp">

    <ImageView
        android:id="@+id/mini_canvas_img"
        android:layout_width="match_parent"
        android:layout_height="match_parent"
        android:scaleType="fitXY"
        android:contentDescription="궁디 플레이어 미니 위젯" />

    <LinearLayout
        android:layout_width="match_parent"
        android:layout_height="match_parent"
        android:orientation="horizontal"
        android:paddingLeft="8dp"
        android:paddingRight="6dp">

        <FrameLayout
            android:id="@+id/mini_hit_open"
            android:layout_width="0dp"
            android:layout_height="match_parent"
            android:layout_weight="54" />

        <FrameLayout
            android:id="@+id/mini_hit_prev"
            android:layout_width="0dp"
            android:layout_height="match_parent"
            android:layout_weight="13" />

        <FrameLayout
            android:id="@+id/mini_hit_play"
            android:layout_width="0dp"
            android:layout_height="match_parent"
            android:layout_weight="15" />

        <FrameLayout
            android:id="@+id/mini_hit_next"
            android:layout_width="0dp"
            android:layout_height="match_parent"
            android:layout_weight="13" />

        <FrameLayout
            android:id="@+id/mini_hit_settings"
            android:layout_width="28dp"
            android:layout_height="match_parent" />
    </LinearLayout>
</FrameLayout>
""")

    # 10. Java: PlaybackStateStore.java (재생 상태 + 진행률 + 위젯 화이트/다크/투명도 설정 저장)
    write_text("app/src/main/java/com/gungdi/player/PlaybackStateStore.java", """
package com.gungdi.player;

import android.content.Context;
import android.content.SharedPreferences;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.util.Base64;

public class PlaybackStateStore {
    private static final String PREF_NAME = "gungdi_widget_prefs_v2";
    public static String currentTitle = "노래를 재생해 보세요";
    public static String currentArtist = "궁디 AI Studio";
    public static boolean isPlaying = false;
    public static Bitmap currentArtwork = null;

    public static long positionMs = 0L;
    public static long durationMs = 0L;
    public static int trackIndex = 1;
    public static int totalTracks = 21;

    // 위젯 커스텀 설정 (기본값: 아이유 스샷처럼 화이트 모드 + 불투명도 92%)
    public static boolean widgetDarkMode = false;
    public static int widgetOpacity = 92;

    public static void save(Context context, String title, String artist, boolean playing, String base64Art) {
        loadIfNeeded(context);
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

    public static void saveProgress(Context context, long pos, long dur, int trackNum, int total) {
        positionMs = Math.max(0L, pos);
        durationMs = Math.max(0L, dur);
        if (trackNum > 0) trackIndex = trackNum;
        if (total > 0) totalTracks = total;

        SharedPreferences prefs = context.getSharedPreferences(PREF_NAME, Context.MODE_PRIVATE);
        prefs.edit()
            .putLong("positionMs", positionMs)
            .putLong("durationMs", durationMs)
            .putInt("trackIndex", trackIndex)
            .putInt("totalTracks", totalTracks)
            .apply();
    }

    public static void saveWidgetStyle(Context context, boolean darkMode, int opacity) {
        widgetDarkMode = darkMode;
        widgetOpacity = Math.max(15, Math.min(100, opacity));
        SharedPreferences prefs = context.getSharedPreferences(PREF_NAME, Context.MODE_PRIVATE);
        prefs.edit()
            .putBoolean("widgetDarkMode", widgetDarkMode)
            .putInt("widgetOpacity", widgetOpacity)
            .apply();
    }

    public static void loadIfNeeded(Context context) {
        SharedPreferences prefs = context.getSharedPreferences(PREF_NAME, Context.MODE_PRIVATE);
        if ("노래를 재생해 보세요".equals(currentTitle)) {
            currentTitle = prefs.getString("title", "노래를 재생해 보세요");
            currentArtist = prefs.getString("artist", "궁디 AI Studio");
            positionMs = prefs.getLong("positionMs", 0L);
            durationMs = prefs.getLong("durationMs", 0L);
            trackIndex = prefs.getInt("trackIndex", 1);
            totalTracks = prefs.getInt("totalTracks", 21);
        }
        widgetDarkMode = prefs.getBoolean("widgetDarkMode", false);
        widgetOpacity = prefs.getInt("widgetOpacity", 92);
    }
}
""")

    # 11. Java: WidgetCanvasRenderer.java (아이유 '라일락' 스타일 고해상도 위젯 & 슬림 위젯 드로잉 엔진)
    write_text("app/src/main/java/com/gungdi/player/WidgetCanvasRenderer.java", """
package com.gungdi.player;

import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.BitmapShader;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.CornerPathEffect;
import android.graphics.LinearGradient;
import android.graphics.Matrix;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.RectF;
import android.graphics.Shader;
import android.graphics.Typeface;
import android.text.TextPaint;
import android.text.TextUtils;

public class WidgetCanvasRenderer {

    /**
     * 1) 아이유 '라일락' 스타일 3x3 앨범 카드형 위젯 렌더링
     * - 둥근 사각형 전체에 앨범 표지 꽉 차게 렌더링
     * - 우측 상단에 반투명 ⚙ 설정 버튼 배치
     * - 하단에 둥근 플로팅 카드(화이트 모드 / 다크 모드 + 투명도 15~100% 반영)
     * - 좌측: 곡 제목, 아티스트, 곡 번호(6/46 스타일)
     * - 우측: 동글동글한 ◀◀, 은은한 광채 원형 ▶/⏸, 동글동글한 ▶▶
     * - 하단 끝: 얇고 세련된 실시간 진행 상태바
     */
    public static Bitmap renderCardWidget(Context context, int widthPx, int heightPx) {
        int w = Math.max(480, widthPx);
        int h = Math.max(480, heightPx);
        Bitmap out = Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888);
        Canvas canvas = new Canvas(out);

        float outerRadius = w * 0.085f;
        RectF outerRect = new RectF(0, 0, w, h);

        // 1. 배경 앨범 표지 그리기 (없으면 피치 그라데이션 + 기본 아이콘)
        Bitmap art = PlaybackStateStore.currentArtwork;
        if (art == null) {
            art = BitmapFactory.decodeResource(context.getResources(), R.mipmap.ic_launcher);
        }

        if (art != null) {
            Paint artPaint = new Paint(Paint.ANTI_ALIAS_FLAG | Paint.FILTER_BITMAP_FLAG);
            BitmapShader shader = new BitmapShader(art, Shader.TileMode.CLAMP, Shader.TileMode.CLAMP);
            Matrix matrix = new Matrix();
            float scale = Math.max(w / (float) art.getWidth(), h / (float) art.getHeight());
            float dx = (w - art.getWidth() * scale) * 0.5f;
            float dy = (h - art.getHeight() * scale) * 0.5f;
            matrix.setScale(scale, scale);
            matrix.postTranslate(dx, dy);
            shader.setLocalMatrix(matrix);
            artPaint.setShader(shader);
            canvas.drawRoundRect(outerRect, outerRadius, outerRadius, artPaint);
        } else {
            Paint gradPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
            gradPaint.setShader(new LinearGradient(0, 0, w, h,
                    Color.parseColor("#FF9A9E"), Color.parseColor("#FECFEF"), Shader.TileMode.CLAMP));
            canvas.drawRoundRect(outerRect, outerRadius, outerRadius, gradPaint);
        }

        // 2. 우측 상단 ⚙ 위젯 설정 아이콘 배지
        float gearCx = w - w * 0.095f;
        float gearCy = h * 0.095f;
        float gearR = w * 0.048f;
        Paint gearBgPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        gearBgPaint.setColor(Color.argb(115, 20, 22, 28));
        canvas.drawCircle(gearCx, gearCy, gearR, gearBgPaint);

        TextPaint gearTextPaint = new TextPaint(Paint.ANTI_ALIAS_FLAG);
        gearTextPaint.setColor(Color.WHITE);
        gearTextPaint.setTextSize(gearR * 1.15f);
        gearTextPaint.setTextAlign(Paint.Align.CENTER);
        Paint.FontMetrics gfm = gearTextPaint.getFontMetrics();
        canvas.drawText("⚙", gearCx, gearCy - (gfm.ascent + gfm.descent) * 0.5f, gearTextPaint);

        // 3. 하단 플로팅 컨트롤 카드 (아이유 라일락 위젯 비율 그대로!)
        float cardMarginX = w * 0.055f;
        float cardMarginBottom = h * 0.055f;
        float cardHeight = h * 0.31f;
        float cardTop = h - cardMarginBottom - cardHeight;
        RectF barRect = new RectF(cardMarginX, cardTop, w - cardMarginX, h - cardMarginBottom);
        float barRadius = cardHeight * 0.25f;

        boolean isDark = PlaybackStateStore.widgetDarkMode;
        int opacityPct = PlaybackStateStore.widgetOpacity;
        int alpha = Math.max(38, Math.min(255, (int) (opacityPct * 2.55f)));

        // 카드 그림자
        Paint shadowPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        shadowPaint.setColor(Color.argb(42, 0, 0, 0));
        RectF shadowRect = new RectF(barRect.left, barRect.top + 6f, barRect.right, barRect.bottom + 6f);
        canvas.drawRoundRect(shadowRect, barRadius, barRadius, shadowPaint);

        // 카드 본체 (화이트 모드 vs 다크 모드 + 사용자 투명도)
        Paint barPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        if (isDark) {
            barPaint.setColor(Color.argb(alpha, 26, 28, 36));
        } else {
            barPaint.setColor(Color.argb(alpha, 255, 255, 255));
        }
        canvas.drawRoundRect(barRect, barRadius, barRadius, barPaint);

        // 4. 좌측 텍스트 영역 (곡 제목 / 아티스트 / 6/46 곡 순서)
        int titleColor = isDark ? Color.WHITE : Color.parseColor("#222328");
        int subColor = isDark ? Color.parseColor("#B4B9C6") : Color.parseColor("#686B73");
        int countColor = isDark ? Color.parseColor("#9096A4") : Color.parseColor("#888B94");

        float textLeft = barRect.left + barRect.width() * 0.068f;
        float maxTextWidth = barRect.width() * 0.42f;

        TextPaint titlePaint = new TextPaint(Paint.ANTI_ALIAS_FLAG);
        titlePaint.setColor(titleColor);
        titlePaint.setTextSize(cardHeight * 0.205f);
        titlePaint.setTypeface(Typeface.create(Typeface.DEFAULT, Typeface.BOLD));
        String safeTitle = TextUtils.ellipsize(
                PlaybackStateStore.currentTitle, titlePaint, maxTextWidth, TextUtils.TruncateAt.END).toString();

        TextPaint artistPaint = new TextPaint(Paint.ANTI_ALIAS_FLAG);
        artistPaint.setColor(subColor);
        artistPaint.setTextSize(cardHeight * 0.155f);
        String safeArtist = TextUtils.ellipsize(
                PlaybackStateStore.currentArtist, artistPaint, maxTextWidth, TextUtils.TruncateAt.END).toString();

        TextPaint countPaint = new TextPaint(Paint.ANTI_ALIAS_FLAG);
        countPaint.setColor(countColor);
        countPaint.setTextSize(cardHeight * 0.132f);
        int idx = Math.max(1, PlaybackStateStore.trackIndex);
        int tot = Math.max(idx, PlaybackStateStore.totalTracks);
        String countStr = idx + "/" + tot;

        float centerY = barRect.centerY() - cardHeight * 0.03f;
        canvas.drawText(safeTitle, textLeft, centerY - cardHeight * 0.14f, titlePaint);
        canvas.drawText(safeArtist, textLeft, centerY + cardHeight * 0.08f, artistPaint);
        canvas.drawText(countStr, textLeft, centerY + cardHeight * 0.27f, countPaint);

        // 5. 우측 컨트롤 버튼 영역 (◀◀ / 광채 원형 ▶·⏸ / ▶▶)
        float controlsCenterY = barRect.centerY() - cardHeight * 0.02f;
        float playCx = barRect.left + barRect.width() * 0.72f;
        float prevCx = barRect.left + barRect.width() * 0.56f;
        float nextCx = barRect.left + barRect.width() * 0.88f;

        // 가운데 광채 원형 재생/일시정지 버튼 (아이유 스샷 스타일!)
        float playRadius = cardHeight * 0.265f;
        Paint haloPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        haloPaint.setColor(Color.argb(46, 232, 118, 148));
        canvas.drawCircle(playCx, controlsCenterY, playRadius * 1.24f, haloPaint);

        Paint playCirclePaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        playCirclePaint.setShader(new LinearGradient(
                playCx - playRadius, controlsCenterY - playRadius,
                playCx + playRadius, controlsCenterY + playRadius,
                Color.parseColor("#E8839B"), Color.parseColor("#BA6B80"),
                Shader.TileMode.CLAMP));
        canvas.drawCircle(playCx, controlsCenterY, playRadius, playCirclePaint);

        // 원 안쪽 둥근 ▶ 또는 ⏸ 아이콘
        drawRoundedPlayOrPause(canvas, playCx, controlsCenterY, playRadius * 0.44f, PlaybackStateStore.isPlaying, Color.WHITE);

        // 양옆 둥근 ◀◀ / ▶▶ 아이콘
        int skipIconColor = isDark ? Color.parseColor("#D8DCE6") : Color.parseColor("#5C5F66");
        float skipSize = cardHeight * 0.135f;
        drawRoundedDoubleSkip(canvas, prevCx, controlsCenterY, skipSize, true, skipIconColor);
        drawRoundedDoubleSkip(canvas, nextCx, controlsCenterY, skipSize, false, skipIconColor);

        // 6. 플로팅 카드 맨 아래 얇은 곡 진행 상태바 (프로그레스바)
        float progLeft = barRect.left + barRect.width() * 0.068f;
        float progRight = barRect.right - barRect.width() * 0.068f;
        float progY = barRect.bottom - cardHeight * 0.105f;
        float progHeight = Math.max(4f, cardHeight * 0.028f);

        Paint trackPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        trackPaint.setColor(isDark ? Color.argb(65, 255, 255, 255) : Color.argb(40, 0, 0, 0));
        RectF trackRect = new RectF(progLeft, progY, progRight, progY + progHeight);
        canvas.drawRoundRect(trackRect, progHeight, progHeight, trackPaint);

        float ratio = 0f;
        if (PlaybackStateStore.durationMs > 0) {
            ratio = Math.max(0f, Math.min(1f, (float) PlaybackStateStore.positionMs / (float) PlaybackStateStore.durationMs));
        }
        if (ratio > 0f) {
            Paint fillPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
            fillPaint.setColor(Color.parseColor("#E26D89"));
            RectF fillRect = new RectF(progLeft, progY, progLeft + (progRight - progLeft) * ratio, progY + progHeight);
            canvas.drawRoundRect(fillRect, progHeight, progHeight, fillPaint);
        }

        return out;
    }

    /**
     * 2) 슬림 가로형 미니 위젯 (4x1) 렌더링 (화이트/다크 모드 + 투명도 동일 적용)
     */
    public static Bitmap renderMiniWidget(Context context, int widthPx, int heightPx) {
        int w = Math.max(680, widthPx);
        int h = Math.max(150, heightPx);
        Bitmap out = Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888);
        Canvas canvas = new Canvas(out);

        boolean isDark = PlaybackStateStore.widgetDarkMode;
        int opacityPct = PlaybackStateStore.widgetOpacity;
        int alpha = Math.max(38, Math.min(255, (int) (opacityPct * 2.55f)));

        RectF barRect = new RectF(4f, 4f, w - 4f, h - 4f);
        float radius = h * 0.34f;

        Paint bgPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        bgPaint.setColor(isDark ? Color.argb(alpha, 25, 27, 35) : Color.argb(alpha, 255, 255, 255));
        canvas.drawRoundRect(bgPaint != null ? barRect : barRect, radius, radius, bgPaint);

        // 테두리
        Paint strokePaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        strokePaint.setStyle(Paint.Style.STROKE);
        strokePaint.setStrokeWidth(2.5f);
        strokePaint.setColor(isDark ? Color.argb(80, 255, 107, 129) : Color.argb(60, 230, 120, 145));
        canvas.drawRoundRect(barRect, radius, radius, strokePaint);

        // 좌측 둥근 앨범 표지
        float artSize = h * 0.72f;
        float artLeft = h * 0.16f;
        float artTop = (h - artSize) * 0.5f;
        RectF artRect = new RectF(artLeft, artTop, artLeft + artSize, artTop + artSize);

        Bitmap art = PlaybackStateStore.currentArtwork;
        if (art == null) {
            art = BitmapFactory.decodeResource(context.getResources(), R.mipmap.ic_launcher);
        }
        if (art != null) {
            Paint artPaint = new Paint(Paint.ANTI_ALIAS_FLAG | Paint.FILTER_BITMAP_FLAG);
            BitmapShader shader = new BitmapShader(art, Shader.TileMode.CLAMP, Shader.TileMode.CLAMP);
            Matrix m = new Matrix();
            float s = Math.max(artSize / art.getWidth(), artSize / art.getHeight());
            m.setScale(s, s);
            m.postTranslate(artLeft + (artSize - art.getWidth() * s) * 0.5f, artTop + (artSize - art.getHeight() * s) * 0.5f);
            shader.setLocalMatrix(m);
            artPaint.setShader(shader);
            canvas.drawRoundRect(artRect, artSize * 0.25f, artSize * 0.25f, artPaint);
        }

        // 곡 제목 & 아티스트
        float textLeft = artRect.right + h * 0.14f;
        float maxTextW = w * 0.38f;
        int titleColor = isDark ? Color.WHITE : Color.parseColor("#222328");
        int subColor = isDark ? Color.parseColor("#B4B9C6") : Color.parseColor("#686B73");

        TextPaint titlePaint = new TextPaint(Paint.ANTI_ALIAS_FLAG);
        titlePaint.setColor(titleColor);
        titlePaint.setTextSize(h * 0.22f);
        titlePaint.setTypeface(Typeface.create(Typeface.DEFAULT, Typeface.BOLD));
        String safeTitle = TextUtils.ellipsize(PlaybackStateStore.currentTitle, titlePaint, maxTextW, TextUtils.TruncateAt.END).toString();

        TextPaint subPaint = new TextPaint(Paint.ANTI_ALIAS_FLAG);
        subPaint.setColor(subColor);
        subPaint.setTextSize(h * 0.16f);
        int idx = Math.max(1, PlaybackStateStore.trackIndex);
        int tot = Math.max(idx, PlaybackStateStore.totalTracks);
        String subStr = PlaybackStateStore.currentArtist + " · " + idx + "/" + tot;
        String safeSub = TextUtils.ellipsize(subStr, subPaint, maxTextW, TextUtils.TruncateAt.END).toString();

        canvas.drawText(safeTitle, textLeft, h * 0.45f, titlePaint);
        canvas.drawText(safeSub, textLeft, h * 0.70f, subPaint);

        // 하단 진행바
        float progY = h * 0.84f;
        float progRight = textLeft + maxTextW;
        Paint trkPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        trkPaint.setColor(isDark ? Color.argb(60, 255, 255, 255) : Color.argb(35, 0, 0, 0));
        canvas.drawRoundRect(new RectF(textLeft, progY, progRight, progY + 5f), 3f, 3f, trkPaint);

        if (PlaybackStateStore.durationMs > 0) {
            float r = Math.max(0f, Math.min(1f, (float) PlaybackStateStore.positionMs / (float) PlaybackStateStore.durationMs));
            Paint flPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
            flPaint.setColor(Color.parseColor("#FF6B81"));
            canvas.drawRoundRect(new RectF(textLeft, progY, textLeft + (progRight - textLeft) * r, progY + 5f), 3f, 3f, flPaint);
        }

        // 우측 컨트롤 버튼 (◀◀ / ▶ / ▶▶) + ⚙
        float cy = h * 0.5f;
        float prevX = w * 0.62f;
        float playX = w * 0.75f;
        float nextX = w * 0.87f;
        float gearX = w * 0.955f;

        float playR = h * 0.27f;
        Paint halo = new Paint(Paint.ANTI_ALIAS_FLAG);
        halo.setColor(Color.argb(45, 232, 118, 148));
        canvas.drawCircle(playX, cy, playR * 1.22f, halo);

        Paint playBg = new Paint(Paint.ANTI_ALIAS_FLAG);
        playBg.setShader(new LinearGradient(playX - playR, cy - playR, playX + playR, cy + playR,
                Color.parseColor("#FF758C"), Color.parseColor("#E8637A"), Shader.TileMode.CLAMP));
        canvas.drawCircle(playX, cy, playR, playBg);
        drawRoundedPlayOrPause(canvas, playX, cy, playR * 0.44f, PlaybackStateStore.isPlaying, Color.WHITE);

        int skipColor = isDark ? Color.parseColor("#D8DCE6") : Color.parseColor("#5C5F66");
        drawRoundedDoubleSkip(canvas, prevX, cy, h * 0.14f, true, skipColor);
        drawRoundedDoubleSkip(canvas, nextX, cy, h * 0.14f, false, skipColor);

        TextPaint gPaint = new TextPaint(Paint.ANTI_ALIAS_FLAG);
        gPaint.setColor(subColor);
        gPaint.setTextSize(h * 0.18f);
        gPaint.setTextAlign(Paint.Align.CENTER);
        Paint.FontMetrics fm = gPaint.getFontMetrics();
        canvas.drawText("⚙", gearX, cy - (fm.ascent + fm.descent) * 0.5f, gPaint);

        return out;
    }

    private static void drawRoundedPlayOrPause(Canvas canvas, float cx, float cy, float size, boolean isPlaying, int color) {
        Paint p = new Paint(Paint.ANTI_ALIAS_FLAG);
        p.setColor(color);
        p.setStyle(Paint.Style.FILL);
        p.setPathEffect(new CornerPathEffect(size * 0.28f));

        if (isPlaying) {
            float barW = size * 0.52f;
            float barH = size * 1.75f;
            float gap = size * 0.28f;
            float r = barW * 0.48f;
            RectF leftBar = new RectF(cx - gap - barW, cy - barH * 0.5f, cx - gap, cy + barH * 0.5f);
            RectF rightBar = new RectF(cx + gap, cy - barH * 0.5f, cx + gap + barW, cy + barH * 0.5f);
            canvas.drawRoundRect(leftBar, r, r, p);
            canvas.drawRoundRect(rightBar, r, r, p);
        } else {
            Path path = new Path();
            float offset = size * 0.15f;
            path.moveTo(cx - size * 0.65f + offset, cy - size * 0.92f);
            path.lineTo(cx + size * 0.95f + offset, cy);
            path.lineTo(cx - size * 0.65f + offset, cy + size * 0.92f);
            path.close();
            canvas.drawPath(path, p);
        }
    }

    private static void drawRoundedDoubleSkip(Canvas canvas, float cx, float cy, float size, boolean isPrev, int color) {
        Paint p = new Paint(Paint.ANTI_ALIAS_FLAG);
        p.setColor(color);
        p.setStyle(Paint.Style.FILL);
        p.setPathEffect(new CornerPathEffect(size * 0.25f));

        float dir = isPrev ? -1f : 1f;
        float triW = size * 0.95f;
        float triH = size * 0.85f;

        // 첫 번째 삼각형
        Path t1 = new Path();
        t1.moveTo(cx, cy);
        t1.lineTo(cx - dir * triW, cy - triH);
        t1.lineTo(cx - dir * triW, cy + triH);
        t1.close();
        canvas.drawPath(t1, p);

        // 두 번째 삼각형 (아이유 라일락 위젯 스타일 ◀◀ / ▶▶)
        Path t2 = new Path();
        t2.moveTo(cx + dir * (triW * 0.88f), cy);
        t2.lineTo(cx - dir * (triW * 0.12f), cy - triH);
        t2.lineTo(cx - dir * (triW * 0.12f), cy + triH);
        t2.close();
        canvas.drawPath(t2, p);
    }
}
""")

    # 12. Java: GungdiWidgetProvider.java (아이유 스타일 3x3 앨범 카드 위젯)
    write_text("app/src/main/java/com/gungdi/player/GungdiWidgetProvider.java", """
package com.gungdi.player;

import android.app.PendingIntent;
import android.appwidget.AppWidgetManager;
import android.appwidget.AppWidgetProvider;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.graphics.Bitmap;
import android.os.Bundle;
import android.widget.RemoteViews;

public class GungdiWidgetProvider extends AppWidgetProvider {

    @Override
    public void onUpdate(Context context, AppWidgetManager appWidgetManager, int[] appWidgetIds) {
        PlaybackStateStore.loadIfNeeded(context);
        for (int appWidgetId : appWidgetIds) {
            updateSingleCardWidget(context, appWidgetManager, appWidgetId);
        }
    }

    @Override
    public void onAppWidgetOptionsChanged(Context context, AppWidgetManager appWidgetManager, int appWidgetId, Bundle newOptions) {
        super.onAppWidgetOptionsChanged(context, appWidgetManager, appWidgetId, newOptions);
        PlaybackStateStore.loadIfNeeded(context);
        updateSingleCardWidget(context, appWidgetManager, appWidgetId);
    }

    public static void updateAllWidgets(Context context) {
        try {
            AppWidgetManager manager = AppWidgetManager.getInstance(context);
            ComponentName cardComp = new ComponentName(context, GungdiWidgetProvider.class);
            int[] cardIds = manager.getAppWidgetIds(cardComp);
            if (cardIds != null) {
                for (int id : cardIds) {
                    updateSingleCardWidget(context, manager, id);
                }
            }
        } catch (Exception ignored) {}
        GungdiMiniWidgetProvider.updateAllMiniWidgets(context);
    }

    public static void updateSingleCardWidget(Context context, AppWidgetManager manager, int appWidgetId) {
        RemoteViews views = new RemoteViews(context.getPackageName(), R.layout.gungdi_card_widget);

        Bitmap rendered = WidgetCanvasRenderer.renderCardWidget(context, 640, 640);
        views.setImageViewBitmap(R.id.card_canvas_img, rendered);

        Intent openIntent = new Intent(context, MainActivity.class);
        openIntent.addFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP | Intent.FLAG_ACTIVITY_CLEAR_TOP);
        PendingIntent openPending = PendingIntent.getActivity(
            context, 100, openIntent,
            PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
        );
        views.setOnClickPendingIntent(R.id.card_hit_open_top, openPending);
        views.setOnClickPendingIntent(R.id.card_hit_open_info, openPending);

        views.setOnClickPendingIntent(R.id.card_hit_settings, buildActionPendingIntent(context, WidgetActionReceiver.ACTION_OPEN_SETTINGS, 104));
        views.setOnClickPendingIntent(R.id.card_hit_prev, buildActionPendingIntent(context, WidgetActionReceiver.ACTION_PREV, 101));
        views.setOnClickPendingIntent(R.id.card_hit_play, buildActionPendingIntent(context, WidgetActionReceiver.ACTION_TOGGLE, 102));
        views.setOnClickPendingIntent(R.id.card_hit_next, buildActionPendingIntent(context, WidgetActionReceiver.ACTION_NEXT, 103));

        manager.updateAppWidget(appWidgetId, views);
    }

    public static PendingIntent buildActionPendingIntent(Context context, String action, int reqCode) {
        Intent intent = new Intent(context, WidgetActionReceiver.class);
        intent.setAction(action);
        return PendingIntent.getBroadcast(
            context, reqCode, intent,
            PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
        );
    }
}
""")

    # 13. Java: GungdiMiniWidgetProvider.java (슬림 가로형 4x1 바 위젯)
    write_text("app/src/main/java/com/gungdi/player/GungdiMiniWidgetProvider.java", """
package com.gungdi.player;

import android.app.PendingIntent;
import android.appwidget.AppWidgetManager;
import android.appwidget.AppWidgetProvider;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.graphics.Bitmap;
import android.os.Bundle;
import android.widget.RemoteViews;

public class GungdiMiniWidgetProvider extends AppWidgetProvider {

    @Override
    public void onUpdate(Context context, AppWidgetManager appWidgetManager, int[] appWidgetIds) {
        PlaybackStateStore.loadIfNeeded(context);
        for (int appWidgetId : appWidgetIds) {
            updateSingleMiniWidget(context, appWidgetManager, appWidgetId);
        }
    }

    @Override
    public void onAppWidgetOptionsChanged(Context context, AppWidgetManager appWidgetManager, int appWidgetId, Bundle newOptions) {
        super.onAppWidgetOptionsChanged(context, appWidgetManager, appWidgetId, newOptions);
        PlaybackStateStore.loadIfNeeded(context);
        updateSingleMiniWidget(context, appWidgetManager, appWidgetId);
    }

    public static void updateAllMiniWidgets(Context context) {
        try {
            AppWidgetManager manager = AppWidgetManager.getInstance(context);
            ComponentName miniComp = new ComponentName(context, GungdiMiniWidgetProvider.class);
            int[] miniIds = manager.getAppWidgetIds(miniComp);
            if (miniIds != null) {
                for (int id : miniIds) {
                    updateSingleMiniWidget(context, manager, id);
                }
            }
        } catch (Exception ignored) {}
    }

    private static void updateSingleMiniWidget(Context context, AppWidgetManager manager, int appWidgetId) {
        RemoteViews views = new RemoteViews(context.getPackageName(), R.layout.gungdi_mini_widget);

        Bitmap rendered = WidgetCanvasRenderer.renderMiniWidget(context, 820, 176);
        views.setImageViewBitmap(R.id.mini_canvas_img, rendered);

        Intent openIntent = new Intent(context, MainActivity.class);
        openIntent.addFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP | Intent.FLAG_ACTIVITY_CLEAR_TOP);
        PendingIntent openPending = PendingIntent.getActivity(
            context, 110, openIntent,
            PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
        );
        views.setOnClickPendingIntent(R.id.mini_hit_open, openPending);

        views.setOnClickPendingIntent(R.id.mini_hit_prev, GungdiWidgetProvider.buildActionPendingIntent(context, WidgetActionReceiver.ACTION_PREV, 111));
        views.setOnClickPendingIntent(R.id.mini_hit_play, GungdiWidgetProvider.buildActionPendingIntent(context, WidgetActionReceiver.ACTION_TOGGLE, 112));
        views.setOnClickPendingIntent(R.id.mini_hit_next, GungdiWidgetProvider.buildActionPendingIntent(context, WidgetActionReceiver.ACTION_NEXT, 113));
        views.setOnClickPendingIntent(R.id.mini_hit_settings, GungdiWidgetProvider.buildActionPendingIntent(context, WidgetActionReceiver.ACTION_OPEN_SETTINGS, 114));

        manager.updateAppWidget(appWidgetId, views);
    }
}
""")

    # 14. Java: WidgetActionReceiver.java
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
    public static final String ACTION_OPEN_SETTINGS = "com.gungdi.player.ACTION_OPEN_SETTINGS";

    @Override
    public void onReceive(Context context, Intent intent) {
        if (intent == null || intent.getAction() == null) return;
        String action = intent.getAction();

        if (ACTION_OPEN_SETTINGS.equals(action)) {
            Intent openSet = new Intent(context, MainActivity.class);
            openSet.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_SINGLE_TOP | Intent.FLAG_ACTIVITY_CLEAR_TOP);
            openSet.putExtra("open_settings", true);
            context.startActivity(openSet);
            return;
        }

        String cmd = "toggle";
        if (ACTION_PREV.equals(action)) cmd = "prev";
        else if (ACTION_NEXT.equals(action)) cmd = "next";
        else if (ACTION_STOP.equals(action)) cmd = "stop";

        if (MainActivity.instance != null) {
            MainActivity.instance.dispatchWidgetCommandToWeb(cmd);
        } else {
            Intent launch = new Intent(context, MainActivity.class);
            launch.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_SINGLE_TOP);
            launch.putExtra("auto_cmd", cmd);
            context.startActivity(launch);
        }
    }
}
""")

    # 15. Java: MediaPlaybackService.java (상단바 & 잠금화면 실시간 진행 상태바 + 드래그 구간 이동 지원!)
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
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.drawable.Icon;
import android.media.MediaMetadata;
import android.media.session.MediaSession;
import android.media.session.PlaybackState;
import android.os.Build;
import android.os.IBinder;
import android.os.PowerManager;

public class MediaPlaybackService extends Service {
    private static final String CHANNEL_ID = "gungdi_media_channel";
    private static final int NOTIF_ID = 777;
    private MediaSession mediaSession;
    private PowerManager.WakeLock wakeLock;

    @Override
    public void onCreate() {
        super.onCreate();
        createChannel();

        PowerManager pm = (PowerManager) getSystemService(Context.POWER_SERVICE);
        if (pm != null) {
            wakeLock = pm.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "GungdiPlayer::AudioWakeLock");
        }

        mediaSession = new MediaSession(this, "GungdiMediaSession");
        mediaSession.setCallback(new MediaSession.Callback() {
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

            @Override
            public void onSeekTo(long pos) {
                if (MainActivity.instance != null) MainActivity.instance.dispatchSeekToWeb(pos);
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
        long actions = PlaybackState.ACTION_PLAY
                | PlaybackState.ACTION_PAUSE
                | PlaybackState.ACTION_PLAY_PAUSE
                | PlaybackState.ACTION_SKIP_TO_NEXT
                | PlaybackState.ACTION_SKIP_TO_PREVIOUS
                | PlaybackState.ACTION_STOP
                | PlaybackState.ACTION_SEEK_TO;

        int state = PlaybackStateStore.isPlaying
                ? PlaybackState.STATE_PLAYING
                : PlaybackState.STATE_PAUSED;

        float speed = PlaybackStateStore.isPlaying ? 1.0f : 0.0f;
        long pos = PlaybackStateStore.positionMs >= 0 ? PlaybackStateStore.positionMs : 0L;

        mediaSession.setPlaybackState(new PlaybackState.Builder()
                .setActions(actions)
                .setState(state, pos, speed)
                .build());

        Bitmap artBmp = PlaybackStateStore.currentArtwork != null
                ? PlaybackStateStore.currentArtwork
                : BitmapFactory.decodeResource(getResources(), R.mipmap.ic_launcher);

        MediaMetadata.Builder metaBuilder = new MediaMetadata.Builder()
                .putString(MediaMetadata.METADATA_KEY_TITLE, PlaybackStateStore.currentTitle)
                .putString(MediaMetadata.METADATA_KEY_ARTIST, PlaybackStateStore.currentArtist)
                .putBitmap(MediaMetadata.METADATA_KEY_ALBUM_ART, artBmp);

        if (PlaybackStateStore.durationMs > 0) {
            metaBuilder.putLong(MediaMetadata.METADATA_KEY_DURATION, PlaybackStateStore.durationMs);
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

        Notification.Action prevAction = new Notification.Action.Builder(
                Icon.createWithResource(this, android.R.drawable.ic_media_previous),
                "이전 곡", prevPending).build();
        Notification.Action toggleAction = new Notification.Action.Builder(
                Icon.createWithResource(this, playPauseIcon),
                playPauseLabel, togglePending).build();
        Notification.Action nextAction = new Notification.Action.Builder(
                Icon.createWithResource(this, android.R.drawable.ic_media_next),
                "다음 곡", nextPending).build();

        Notification.MediaStyle mediaStyle = new Notification.MediaStyle()
                .setMediaSession(mediaSession.getSessionToken())
                .setShowActionsInCompactView(0, 1, 2);

        return new Notification.Builder(this, CHANNEL_ID)
                .setSmallIcon(R.mipmap.ic_launcher)
                .setLargeIcon(artBmp)
                .setContentTitle(PlaybackStateStore.currentTitle)
                .setContentText(PlaybackStateStore.currentArtist)
                .setContentIntent(contentIntent)
                .setVisibility(Notification.VISIBILITY_PUBLIC)
                .setOngoing(PlaybackStateStore.isPlaying)
                .addAction(prevAction)
                .addAction(toggleAction)
                .addAction(nextAction)
                .setStyle(mediaStyle)
                .build();
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

    # 16. Java: BackgroundAudioWebView.java
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
        super.onWindowVisibilityChanged(View.VISIBLE);
    }
}
""")

    # 17. Java: MainActivity.java
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
import android.view.Window;
import android.webkit.JavascriptInterface;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

public class MainActivity extends Activity {
    public static MainActivity instance;
    private static final String APP_URL = "https://dg1682-commits.github.io/goongdyplay/";
    private static final int FILE_CHOOSER_REQ_CODE = 9001;

    private BackgroundAudioWebView webView;
    private ValueCallback<Uri[]> filePathCallback;
    private String pendingAutoCommand = null;
    private boolean pendingOpenSettings = false;

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
        PlaybackStateStore.loadIfNeeded(this);

        if (getIntent() != null) {
            if (getIntent().hasExtra("auto_cmd")) {
                pendingAutoCommand = getIntent().getStringExtra("auto_cmd");
            }
            if (getIntent().getBooleanExtra("open_settings", false)) {
                pendingOpenSettings = true;
            }
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
                if (pendingOpenSettings) {
                    pendingOpenSettings = false;
                    webView.postDelayed(() -> openSettingsInWeb(), 400);
                }
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

        webView.loadUrl(APP_URL);
        GungdiWidgetProvider.updateAllWidgets(this);
    }

    @Override
    @SuppressWarnings("deprecation")
    public void onBackPressed() {
        if (webView != null) {
            webView.evaluateJavascript(
                "if (window.handleAndroidBackKey) { window.handleAndroidBackKey(); } else { navigateBack(true); }",
                null
            );
        } else {
            super.onBackPressed();
        }
    }

    @Override
    protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        setIntent(intent);
        if (intent != null) {
            if (intent.getBooleanExtra("open_settings", false)) {
                openSettingsInWeb();
            }
            if (intent.hasExtra("auto_cmd")) {
                String cmd = intent.getStringExtra("auto_cmd");
                if (cmd != null) {
                    dispatchWidgetCommandToWeb(cmd);
                }
            }
        }
    }

    private void openSettingsInWeb() {
        runOnUiThread(() -> {
            if (webView != null) {
                webView.evaluateJavascript(
                    "if (typeof showView === 'function') { showView('settingsView'); }",
                    null
                );
            }
        });
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

    public void dispatchSeekToWeb(final long posMs) {
        runOnUiThread(() -> {
            if (webView != null) {
                webView.evaluateJavascript(
                    "if (window.handleAndroidSeekTo) { window.handleAndroidSeekTo(" + posMs + "); }",
                    null
                );
            }
        });
    }

    private void requestNotificationPermissionIfNeeded() {
        if (Build.VERSION.SDK_INT >= 33) {
            if (checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)
                    != PackageManager.PERMISSION_GRANTED) {
                requestPermissions(
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

    private void triggerMediaServiceUpdate() {
        Intent serviceIntent = new Intent(MainActivity.this, MediaPlaybackService.class);
        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                startForegroundService(serviceIntent);
            } else {
                startService(serviceIntent);
            }
        } catch (Exception ignored) {}
    }

    public class AndroidBridge {
        @JavascriptInterface
        public void updatePlaybackState(String title, String artist, boolean isPlaying, String base64Art) {
            PlaybackStateStore.save(MainActivity.this, title, artist, isPlaying, base64Art);
            GungdiWidgetProvider.updateAllWidgets(MainActivity.this);
            triggerMediaServiceUpdate();
        }

        @JavascriptInterface
        public void updatePlaybackProgress(long posMs, long durMs, int trackNum, int totalTracks) {
            PlaybackStateStore.saveProgress(MainActivity.this, posMs, durMs, trackNum, totalTracks);
            GungdiWidgetProvider.updateAllWidgets(MainActivity.this);
            triggerMediaServiceUpdate();
        }

        @JavascriptInterface
        public void updateWidgetStyle(boolean darkMode, int opacity) {
            PlaybackStateStore.saveWidgetStyle(MainActivity.this, darkMode, opacity);
            GungdiWidgetProvider.updateAllWidgets(MainActivity.this);
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

                finishAndRemoveTask();
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

    # 18. 앱 아이콘 복사
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

    print("Android native project (IU Card Widget + Slim Widget) generated at:", ANDROID_DIR)


if __name__ == "__main__":
    main()
