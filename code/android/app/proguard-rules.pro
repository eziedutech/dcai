-keepattributes *Annotation*, InnerClasses
-keep,includedescriptorclasses class dev.eziedutech.dcai.guardian.**$$serializer { *; }
-keepclassmembers class dev.eziedutech.dcai.guardian.** { *** Companion; }

# ExecuTorch runtime: JNI-bound classes and the LLM extension must not be renamed or stripped.
-keep class org.pytorch.executorch.** { *; }
-keep class com.facebook.jni.** { *; }
-keepclasseswithmembernames class * { native <methods>; }

# ML Kit finds its components by instantiating the registrars named in the manifest by
# reflection. Without their no-arg constructors (stripped by R8 full mode) no component
# registers and every InputImage call crashes.
-keep class * implements com.google.firebase.components.ComponentRegistrar { <init>(); }
