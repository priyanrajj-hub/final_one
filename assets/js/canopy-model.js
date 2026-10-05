/**
 * CANOPY AI: Custom Convolutional Neural Network (CNN) architecture
 * Utilizes TensorFlow.js to perform Transfer Learning on top of MobileNet
 * Optimized for classifying agricultural datasets (Healthy, Early Blight, Late Blight).
 */

class CanopyTransferModel {
    constructor() {
        this.baseModel = null;
        this.cropModel = null;
        this.isCompiled = false;
        this.classes = ["Healthy", "Early Blight", "Late Blight", "Non-Vegetation"];
    }

    /**
     * Initializes the CNN network. Stubs off the MobileNet image-net classification head
     * and attaches a specialized Multi-Layer Perceptron (MLP) for PlantVillage vectors.
     */
    async initialize() {
        try {
            console.log("[CANOPY ML] Downloading MobileNet Base Tensors...");
            // Load base MobileNet (feature extractor)
            const mobilenet = await tf.loadLayersModel('https://storage.googleapis.com/tfjs-models/tfjs/mobilenet_v1_0.25_224/model.json');

            // Re-route the output from an intermediate activation layer instead of final 1000-class softmax
            const layer = mobilenet.getLayer('conv_pw_13_relu');
            this.baseModel = tf.model({ inputs: mobilenet.inputs, outputs: layer.output });

            // Freeze base model weights so we only train the custom classifier head
            for (const l of this.baseModel.layers) {
                l.trainable = false;
            }

            console.log("[CANOPY ML] Compiling Custom Dense Architecture...");
            this.cropModel = tf.sequential({
                layers: [
                    // Flatten the 2D convolutions into a 1D vector
                    tf.layers.flatten({ inputShape: this.baseModel.outputs[0].shape.slice(1) }),

                    // Hidden layer for complex non-linear plant features
                    tf.layers.dense({
                        units: 128,
                        activation: 'relu',
                        kernelInitializer: 'varianceScaling',
                        useBias: true
                    }),

                    // Dropout for regularization (preventing overfitting on leaves)
                    tf.layers.dropout({ rate: 0.3 }),

                    // Final classification head
                    tf.layers.dense({
                        units: this.classes.length,
                        activation: 'softmax',
                        kernelInitializer: 'varianceScaling',
                        useBias: false
                    })
                ]
            });

            // Compile the optimizer
            this.cropModel.compile({
                optimizer: tf.train.adam(0.0001),
                loss: 'categoricalCrossentropy',
                metrics: ['accuracy']
            });

            this.isCompiled = true;
            console.log("[CANOPY ML] Custom CNN Architecture successfully compiled.");
            return true;
        } catch (e) {
            console.error("[CANOPY ML] Neural Network Initialization Failed:", e);
            return false;
        }
    }

    /**
     * Run an actual tensor classification against a given HTML Image element or canvas
     */
    async predict(imgElement) {
        if (!this.isCompiled) {
            throw new Error("Model not initialized. Awaiting tensor compilation.");
        }

        const logits = tf.tidy(() => {
            // Convert pixels to tensor, resize to 224x224, and normalize [-1, 1]
            let img = tf.browser.fromPixels(imgElement)
                .resizeNearestNeighbor([224, 224])
                .toFloat();

            const offset = tf.scalar(127.5);
            const normalized = img.sub(offset).div(offset).expandDims();

            // Extract features through MobileNet base
            const features = this.baseModel.predict(normalized);

            // Classify via our custom Dense crop head
            return this.cropModel.predict(features);
        });

        // Resolve top probability
        const probs = await logits.data();
        let maxIndex = -1;
        let maxProb = -1;
        for (let i = 0; i < probs.length; i++) {
            if (probs[i] > maxProb) {
                maxProb = probs[i];
                maxIndex = i;
            }
        }

        logits.dispose();

        return {
            class: this.classes[maxIndex],
            confidence: Math.round(maxProb * 100)
        };
    }
}

window.CanopyTransferModel = CanopyTransferModel;
