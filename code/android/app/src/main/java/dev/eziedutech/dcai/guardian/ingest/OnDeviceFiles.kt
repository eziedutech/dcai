package dev.eziedutech.dcai.guardian.ingest

import android.content.Context
import java.io.File

/**
 * Where the on-device stage 1 model lives on the phone. Shared by the main process (which
 * downloads it) and the :ondevice process (which loads it): app storage is per app, so both
 * processes see the same files. noBackupFilesDir is sandboxed and never leaves in a cloud backup.
 */
object OnDeviceFiles {
    const val DIR = "ondevice"
    const val PTE = "stage1.pte"
    const val TOK = "tokenizer.json"
    // Written only after both files verify against the manifest; holds the installed version.
    const val OK = "installed.json"

    fun dir(context: Context): File = File(context.applicationContext.noBackupFilesDir, DIR)
    fun pte(context: Context): File = File(dir(context), PTE)
    fun tok(context: Context): File = File(dir(context), TOK)
    fun ok(context: Context): File = File(dir(context), OK)

    fun installed(context: Context): Boolean =
        pte(context).isFile && tok(context).isFile && ok(context).isFile
}
