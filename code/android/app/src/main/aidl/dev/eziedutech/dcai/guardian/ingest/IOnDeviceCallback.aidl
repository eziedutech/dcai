package dev.eziedutech.dcai.guardian.ingest;

// Result of one on-device generate, delivered back to the main process. oneway: the model
// process never blocks on the caller.
interface IOnDeviceCallback {
    oneway void onResult(String text);
    oneway void onError(String reason);
}
