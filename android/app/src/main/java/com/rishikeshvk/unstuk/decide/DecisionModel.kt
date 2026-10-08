package com.rishikeshvk.unstuk.decide

import ai.onnxruntime.OnnxTensor
import ai.onnxruntime.OrtEnvironment
import ai.onnxruntime.OrtSession
import android.content.res.AssetManager
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.nio.LongBuffer
import java.nio.channels.FileChannel
import kotlinx.serialization.json.Json

/**
 * The decision model on the phone (M7): bge's tokenizer, the int8 graph on ONNX Runtime, then M6's heads. Its
 * only output is a probability per catalog intent and for out of scope (AGENTS.md invariant 1).
 */
class DecisionModel private constructor(
    private val session: OrtSession,
    private val wordPiece: WordPiece,
    private val head: DecisionHead,
    val manifest: ModelManifest
) : AutoCloseable {
    /** [state] is [StateText]'s rendering; empty means the complaint is encoded alone, as in training. */
    fun decide(complaint: String, state: String): IntentChoice {
        val tokens = wordPiece.encode(complaint, state.ifEmpty { null })
        val shape = longArrayOf(1, tokens.ids.size.toLong())
        val env = OrtEnvironment.getEnvironment()
        val inputs = mapOf(
            "input_ids" to tokens.ids,
            "attention_mask" to LongArray(tokens.ids.size) { 1L },
            "token_type_ids" to tokens.typeIds
        ).mapValues { (_, values) -> OnnxTensor.createTensor(env, LongBuffer.wrap(values), shape) }
        try {
            session.run(inputs).use { result ->
                @Suppress("UNCHECKED_CAST")
                val vector = (result.get("vector").get().value as Array<FloatArray>)[0]
                val noul = (result.get("noul_logit").get().value as FloatArray)[0]
                return head.decide(vector, noul)
            }
        } finally {
            inputs.values.forEach(OnnxTensor::close)
        }
    }

    override fun close() = session.close()

    companion object {
        private const val DIR = "model"
        private val json = Json { ignoreUnknownKeys = true }

        /** Slow (about a second): call it off the main thread, once. */
        fun load(assets: AssetManager): DecisionModel {
            val manifest = json.decodeFromString<ModelManifest>(assets.text("$DIR/model.json"))
            val vocab = assets.open("$DIR/vocab.txt").bufferedReader().use { it.readLines() }
            val options = optionVectors(assets.bytes("$DIR/options.bin"), manifest.dimensions)
            val session = OrtEnvironment.getEnvironment()
                .createSession(mapped(assets, "$DIR/decision.onnx"), OrtSession.SessionOptions())
            return DecisionModel(
                session,
                WordPiece(vocab, manifest.maxTokens),
                DecisionHead(manifest, options),
                manifest
            )
        }

        private fun optionVectors(bytes: ByteArray, dimensions: Int): List<FloatArray> {
            val floats = ByteBuffer.wrap(bytes).order(ByteOrder.LITTLE_ENDIAN).asFloatBuffer()
            return List(floats.remaining() / dimensions) {
                FloatArray(dimensions).also(floats::get)
            }
        }

        // The graph is stored uncompressed, so it can be mapped from the APK instead of copied onto the heap.
        private fun mapped(assets: AssetManager, name: String): ByteBuffer {
            val fd = assets.openFd(name)
            // The stream owns the descriptor; the mapping outlives both.
            return fd.createInputStream().use { stream ->
                stream.channel.map(FileChannel.MapMode.READ_ONLY, fd.startOffset, fd.declaredLength)
            }
        }

        private fun AssetManager.text(name: String) = open(name).bufferedReader().use {
            it.readText()
        }

        private fun AssetManager.bytes(name: String) = open(name).use { it.readBytes() }
    }
}
