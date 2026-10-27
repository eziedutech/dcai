package dev.eziedutech.dcai.guardian.privacy

import java.security.MessageDigest
import java.security.SecureRandom
import javax.crypto.SecretKeyFactory
import javax.crypto.spec.PBEKeySpec

/**
 * The parent's PIN, set during pairing. Only a salted PBKDF2 hash is kept. It gates the
 * review of a blurred image on the child's phone.
 */
object Pin {
    private const val ITERATIONS = 60_000
    private val PATTERN = Regex("^[0-9]{4,8}$")

    fun valid(pin: String) = PATTERN.matches(pin)

    fun newSalt(): ByteArray = ByteArray(16).also { SecureRandom().nextBytes(it) }

    fun hash(pin: String, salt: ByteArray): ByteArray {
        val spec = PBEKeySpec(pin.toCharArray(), salt, ITERATIONS, 256)
        try {
            return SecretKeyFactory.getInstance("PBKDF2WithHmacSHA256").generateSecret(spec).encoded
        } finally {
            spec.clearPassword()
        }
    }

    fun matches(pin: String, salt: ByteArray, expected: ByteArray): Boolean =
        valid(pin) && MessageDigest.isEqual(hash(pin, salt), expected)
}
