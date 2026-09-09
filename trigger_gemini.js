require('dotenv').config();
const handler = require('./api/gemini/index.js');

const req = {
    headers: { 'x-forwarded-for': '127.0.0.1' },
    body: { prompt: "Hello, this is a test prompt." }
};

const res = {
    status: function (code) {
        this.statusCode = code;
        return this;
    },
    json: function (data) {
        console.log(`[Response ${this.statusCode}]`, data);
        return this;
    }
};

(async () => {
    console.log("Invoking Gemini API handler...");
    await handler(req, res);
    console.log("Done.");
})();
