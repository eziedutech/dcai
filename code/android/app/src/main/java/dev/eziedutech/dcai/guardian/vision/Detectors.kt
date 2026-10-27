package dev.eziedutech.dcai.guardian.vision

import android.graphics.Bitmap
import android.graphics.Rect
import com.google.android.gms.tasks.Tasks
import com.google.mlkit.vision.common.InputImage
import com.google.mlkit.vision.face.FaceDetection
import com.google.mlkit.vision.face.FaceDetectorOptions
import com.google.mlkit.vision.text.TextRecognition
import com.google.mlkit.vision.text.latin.TextRecognizerOptions

/**
 * The slot for a sensitive-image classifier (sexual content, violence). It runs on the
 * phone; the image never leaves it.
 *
 * No model ships with this build. A model is plugged in by implementing this interface
 * with a licensed classifier and registering it in ServiceLocator. Its accuracy is the
 * figure its source states; dcAI has not measured it, and we do not create or collect
 * sensitive images to test one. Until a model is installed, installed is false, the
 * transparency screen says so, and only faces and personal text are detected.
 */
interface SensitiveModel {
    val installed: Boolean

    /** The highest-scoring sensitive category, or null when nothing scores. */
    fun score(bitmap: Bitmap): SensitiveScore?
}

object NoSensitiveModel : SensitiveModel {
    override val installed = false
    override fun score(bitmap: Bitmap): SensitiveScore? = null
}

/**
 * Faces and text, found with ML Kit's bundled on-device models: no network call, the
 * models ship inside the app. Call off the main thread.
 */
class OnDeviceDetectors(private val sensitive: SensitiveModel) {
    private val faceClient by lazy {
        FaceDetection.getClient(
            FaceDetectorOptions.Builder()
                .setPerformanceMode(FaceDetectorOptions.PERFORMANCE_MODE_FAST)
                .setMinFaceSize(0.08f)
                .build(),
        )
    }
    private val textClient by lazy { TextRecognition.getClient(TextRecognizerOptions.DEFAULT_OPTIONS) }

    data class Result(val findings: Findings, val blocks: List<OcrBlock>)

    fun run(bitmap: Bitmap, knownNames: List<String>, wantFaces: Boolean): Result {
        val image = InputImage.fromBitmap(bitmap, 0)
        val w = bitmap.width.toFloat()
        val h = bitmap.height.toFloat()
        fun box(r: Rect?): Box =
            if (r == null) Box(0f, 0f, 1f, 1f)
            else Box((r.left / w).coerceIn(0f, 1f), (r.top / h).coerceIn(0f, 1f), (r.right / w).coerceIn(0f, 1f), (r.bottom / h).coerceIn(0f, 1f))

        val text = Tasks.await(textClient.process(image))
        val blocks = text.textBlocks.map { b ->
            OcrBlock(b.text, box(b.boundingBox), b.lines.map { OcrLine(it.text, box(it.boundingBox)) })
        }
        val faces = if (wantFaces) Tasks.await(faceClient.process(image)).map { box(it.boundingBox) } else emptyList()
        val findings = Findings(
            faces = faces,
            personalText = OcrText.personalRegions(blocks, knownNames),
            sensitive = sensitive.score(bitmap),
            detectorVersion = VERSION,
        )
        return Result(findings, blocks)
    }

    companion object {
        /** The ML Kit artifacts in app/build.gradle.kts, plus the shared masking rules. */
        const val VERSION = "mlkit-face-16.1.7+text-16.0.1+mask"
    }
}
