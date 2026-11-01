-keepattributes *Annotation*, InnerClasses
-keep,includedescriptorclasses class dev.eziedutech.dcai.guardian.**$$serializer { *; }
-keepclassmembers class dev.eziedutech.dcai.guardian.** { *** Companion; }

# ExecuTorch runtime: JNI-bound classes and the LLM extension must not be renamed or stripped.
-keep class org.pytorch.executorch.** { *; }
-keep class com.facebook.jni.** { *; }
-keepclasseswithmembernames class * { native <methods>; }
