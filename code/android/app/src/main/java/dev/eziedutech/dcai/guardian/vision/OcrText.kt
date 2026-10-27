package dev.eziedutech.dcai.guardian.vision

import dev.eziedutech.dcai.guardian.privacy.Mask

/** Text recognised on the phone, in the shape the detector returns (blocks of lines). */
data class OcrLine(val text: String, val box: Box)

data class OcrBlock(val text: String, val box: Box, val lines: List<OcrLine>)

/**
 * Personal data in an image's text, found with the same masking rules as chat messages.
 * Pure Kotlin so it is tested without a phone.
 */
object OcrText {
    /**
     * Regions to blur: each line that holds personal data, or the whole block when the data
     * only shows up across lines (an address broken over two lines).
     */
    fun personalRegions(blocks: List<OcrBlock>, knownNames: List<String> = emptyList()): List<Box> =
        blocks.flatMap { block ->
            val lines = block.lines.filter { Mask.find(normalize(it.text), knownNames).isNotEmpty() }.map { it.box }
            when {
                lines.isNotEmpty() -> lines
                Mask.find(normalize(block.text), knownNames).isNotEmpty() -> listOf(block.box)
                else -> emptyList()
            }
        }

    /** All recognised text, for the conversation's assessment (masked in MessageIngest). */
    fun joined(blocks: List<OcrBlock>): String = normalize(blocks.joinToString("\n") { it.text }.trim())

    /**
     * Fixes OCR misreads that hide personal data from the masking rules: a lowercase l read
     * as a capital I or a 1 in the street prefix ("JI. Mawar" for "Jl. Mawar").
     */
    fun normalize(text: String): String = STREET_MISREAD.replace(text, "Jl")

    private val STREET_MISREAD = Regex("""(?<![A-Za-z])J[I1|](?=n?\.?\s)""")
}
