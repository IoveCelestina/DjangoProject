// src/api/attendanceSync.js
import { get, post } from "@/util/request";

// snake_case -> camelCase
function toCamelKey(key) {
    return key.replace(/_([a-z])/g, (_, c) => c.toUpperCase());
}

function isPlainObject(v) {
    return Object.prototype.toString.call(v) === "[object Object]";
}

function toCamel(obj) {
    if (Array.isArray(obj)) return obj.map(toCamel);
    if (!isPlainObject(obj)) return obj;

    const out = {};
    Object.keys(obj).forEach((k) => {
        out[toCamelKey(k)] = toCamel(obj[k]);
    });
    return out;
}

function unwrapAxios(resp) {
    // 你的 request.js resolve 的是 axios response
    return resp?.data || {};
}

function unwrapAndCamel(resp) {
    const payload = unwrapAxios(resp); // {code,msg,data}
    if (!payload || typeof payload !== "object") return payload;
    if (payload.data) payload.data = toCamel(payload.data);
    return payload;
}

export function apiGetPipelineState() {
    // 注意：你的 baseUrl 末尾有 /，这里不要再用 / 开头，避免双斜杠
    return get("bsns/attendance/admin/pipeline/state").then(unwrapAndCamel);
}

export function apiSaveTrustCode({ trustCode, runPipeline = true }) {
    return post("bsns/attendance/admin/trust_code", {
        trust_code: trustCode,
        run_pipeline: runPipeline,
    }).then(unwrapAndCamel);
}

export function apiRunPipeline() {
    return post("bsns/attendance/admin/pipeline/run", {}).then(unwrapAndCamel);
}

export function apiGetJobs({ pageNum = 1, pageSize = 20 } = {}) {
    return get("bsns/attendance/admin/pipeline/jobs", {
        page_num: pageNum,
        page_size: pageSize,
    }).then(unwrapAndCamel);
}

export function apiGetJobDetail(jobId) {
    return get(`bsns/attendance/admin/pipeline/jobs/${jobId}`).then(unwrapAndCamel);
}
