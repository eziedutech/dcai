package dev.eziedutech.dcai.guardian.ingest;

import dev.eziedutech.dcai.guardian.ingest.IOnDeviceCallback;

// The on-device model, hosted in a separate (:ondevice) process so an out-of-memory kill of the
// heavy model takes only that process, not the dcAI UI and accessibility service.
interface IOnDeviceModel {
    oneway void generate(String prompt, in IOnDeviceCallback callback);
}
