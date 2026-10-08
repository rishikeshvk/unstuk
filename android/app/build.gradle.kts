import groovy.json.JsonSlurper
import java.io.OutputStream
import java.security.DigestInputStream
import java.security.MessageDigest

plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.compose)
    alias(libs.plugins.kotlin.serialization)
    alias(libs.plugins.ktlint)
}

android {
    namespace = "com.rishikeshvk.unstuk"
    compileSdk {
        version = release(37)
    }

    defaultConfig {
        applicationId = "com.rishikeshvk.unstuk"
        minSdk = 29
        targetSdk = 37
        versionCode = 1
        versionName = "1.0"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
        // ONNX Runtime's native library is the largest thing after the model; phones in scope are arm64.
        ndk { abiFilters += "arm64-v8a" }
    }

    buildTypes {
        release {
            optimization {
                enable = true
                packageScope = setOf("androidx.**", "kotlin.**", "kotlinx.**")
            }
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_11
        targetCompatibility = JavaVersion.VERSION_11
    }
    buildFeatures {
        compose = true
        buildConfig = true
    }
    androidResources {
        // Stored, not deflated, so the model is read straight from the APK without an inflated copy.
        noCompress += listOf("onnx", "bin")
    }
    sourceSets {
        // The catalog's single source of truth sits at the repo root, where training code reads it too.
        getByName("main").assets.srcDir(rootProject.file("../catalog"))
    }
}

dependencies {
    implementation(platform(libs.androidx.compose.bom))
    implementation(libs.androidx.activity.compose)
    implementation(libs.androidx.compose.material3)
    implementation(libs.androidx.compose.ui)
    implementation(libs.androidx.compose.ui.graphics)
    implementation(libs.androidx.compose.ui.tooling.preview)
    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.lifecycle.runtime.compose)
    implementation(libs.androidx.lifecycle.process)
    implementation(libs.androidx.lifecycle.viewmodel.compose)
    implementation(libs.kotlinx.serialization.json)
    implementation(libs.onnxruntime.android)
    implementation(libs.androidx.lifecycle.runtime.ktx)
    testImplementation(libs.junit)
    androidTestImplementation(platform(libs.androidx.compose.bom))
    androidTestImplementation(libs.androidx.compose.ui.test.junit4)
    androidTestImplementation(libs.androidx.espresso.core)
    androidTestImplementation(libs.androidx.junit)
    debugImplementation(libs.androidx.compose.ui.test.manifest)
    debugImplementation(libs.androidx.compose.ui.tooling)
}

/** Refuses model files that are missing or differ from what `unstuk-export assets` pinned (M7 spec section 5). */
abstract class CheckModelAssets : DefaultTask() {
    @get:InputDirectory
    @get:PathSensitive(PathSensitivity.RELATIVE)
    abstract val modelDir: DirectoryProperty

    @get:InputFile
    @get:PathSensitive(PathSensitivity.RELATIVE)
    abstract val intents: RegularFileProperty

    @get:OutputFile
    abstract val stamp: RegularFileProperty

    @TaskAction
    fun check() {
        val dir = modelDir.get().asFile
        val manifest = JsonSlurper().parse(dir.resolve("model.json")) as Map<*, *>
        val pinned = mapOf(
            "decision.onnx" to "graph_sha256",
            "options.bin" to "options_sha256",
            "vocab.txt" to "vocab_sha256"
        )
        val stale = pinned.filter { (name, key) ->
            val file = dir.resolve(name)
            !file.exists() || sha256(file) != manifest[key]
        }.keys.toMutableList()
        if (sha256(intents.get().asFile) != manifest["catalog_sha256"]) {
            stale += "catalog/intents.json (changed since export)"
        }
        if (stale.isNotEmpty()) {
            throw GradleException(
                "Model assets missing or stale: ${stale.joinToString()}. Run `uv run unstuk-export assets` in ml/."
            )
        }
        stamp.get().asFile.writeText(manifest["graph_sha256"].toString())
    }

    private fun sha256(file: File): String {
        val digest = MessageDigest.getInstance("SHA-256")
        DigestInputStream(file.inputStream(), digest).use { stream ->
            stream.copyTo(OutputStream.nullOutputStream())
        }
        return digest.digest().joinToString("") { byte -> "%02x".format(byte) }
    }
}

val checkModelAssets = tasks.register<CheckModelAssets>("checkModelAssets") {
    modelDir = layout.projectDirectory.dir("src/main/assets/model")
    intents = rootProject.layout.projectDirectory.file("../catalog/intents.json")
    stamp = layout.buildDirectory.file("checkModelAssets/stamp")
}

tasks.named("preBuild") { dependsOn(checkModelAssets) }
