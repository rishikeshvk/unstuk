# ONNX Runtime's native code finds its Java classes by name over JNI, so R8 must not rename or remove them.
-keep class ai.onnxruntime.** { *; }
