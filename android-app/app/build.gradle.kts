plugins {
  id("com.android.application")
  id("org.jetbrains.kotlin.android")
}

android {
  namespace = "com.edumind.mobile"
  compileSdk = 34

  defaultConfig {
    applicationId = "com.edumind.mobile"
    minSdk = 24
    targetSdk = 34
    versionCode = 1
    versionName = "0.1.0"
  }

  buildTypes {
    debug {
      isMinifyEnabled = false
      buildConfigField("String", "WEB_APP_URL", "\"file:///android_asset/index.html\"")
      buildConfigField("String", "WEB_API_BASE_URL", "\"\"")
      buildConfigField("boolean", "WEB_APP_CLEAR_TEXT", "true")
    }
    release {
      isMinifyEnabled = false
      buildConfigField("String", "WEB_APP_URL", "\"file:///android_asset/index.html\"")
      buildConfigField("String", "WEB_API_BASE_URL", "\"\"")
      buildConfigField("boolean", "WEB_APP_CLEAR_TEXT", "true")
      proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
    }
  }

  buildFeatures {
    buildConfig = true
  }

  compileOptions {
    sourceCompatibility = JavaVersion.VERSION_17
    targetCompatibility = JavaVersion.VERSION_17
  }
  kotlinOptions {
    jvmTarget = "17"
  }
}

dependencies {
  implementation("androidx.activity:activity-ktx:1.8.2")
  implementation("androidx.core:core-ktx:1.12.0")
  implementation("androidx.appcompat:appcompat:1.6.1")
  implementation("com.google.android.material:material:1.11.0")
}
