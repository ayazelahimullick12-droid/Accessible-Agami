import javax.inject.Inject

plugins {
    id("com.android.application")
}

android {
    namespace = "com.accessibleagami.app"
    compileSdk = 36

    defaultConfig {
        applicationId = "com.accessibleagami.app"
        minSdk = 23
        targetSdk = 36
        versionCode = 1
        versionName = "1.0"
    }

    buildTypes {
        release {
            isMinifyEnabled = false
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}

// The app itself is ../../agami.html + ../../assets (the same files Render
// serves). They are copied into the APK's assets on every build, so editing
// agami.html or adding a recording needs no change here: just rebuild.
abstract class CopyWebApp : DefaultTask() {
    @get:InputFile abstract val page: RegularFileProperty
    @get:InputDirectory abstract val assetsDir: DirectoryProperty
    @get:OutputDirectory abstract val outputDir: DirectoryProperty
    @get:Inject abstract val fs: FileSystemOperations

    @TaskAction
    fun copy() {
        fs.sync {
            from(page)
            from(assetsDir) {
                into("assets")
                exclude("**/*.txt", "**/*.md")
            }
            into(outputDir)
        }
    }
}

val copyWebApp = tasks.register<CopyWebApp>("copyWebApp") {
    val repoRoot = rootProject.layout.projectDirectory.dir("..")
    page.set(repoRoot.file("agami.html"))
    assetsDir.set(repoRoot.dir("assets"))
}

androidComponents {
    onVariants { variant ->
        variant.sources.assets?.addGeneratedSourceDirectory(copyWebApp, CopyWebApp::outputDir)
    }
}
