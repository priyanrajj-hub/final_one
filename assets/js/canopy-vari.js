/**
 * CANOPY AI: Visible Atmospherically Resistant Index (VARI) Module.
 * Directly extracts true NDVI-proxy values mathematically from the live satellite imagery.
 */
class CanopyVARI {
    static async calculateFromTile(lat, lon, zoom = 18) {
        return new Promise((resolve, reject) => {
            try {
                // Calculate slippy map XYZ coordinates
                const tx = Math.floor((lon + 180) / 360 * Math.pow(2, zoom));
                const ty = Math.floor((1 - Math.log(Math.tan(lat * Math.PI / 180) + 1 / Math.cos(lat * Math.PI / 180)) / Math.PI) / 2 * Math.pow(2, zoom));

                const img = new Image();
                img.crossOrigin = "anonymous";
                img.src = `/api/proxy-tile?x=${tx}&y=${ty}&z=${zoom}`;

                img.onload = () => {
                    const canvas = document.createElement('canvas');
                    canvas.width = 256;
                    canvas.height = 256;
                    const ctx = canvas.getContext('2d');
                    ctx.drawImage(img, 0, 0);

                    const imgData = ctx.getImageData(0, 0, 256, 256).data;
                    let totalVARI = 0;
                    let validPixels = 0;

                    for (let i = 0; i < imgData.length; i += 4) {
                        const r = imgData[i];
                        const g = imgData[i + 1];
                        const b = imgData[i + 2];

                        // VARI Formula: (Green - Red) / (Green + Red - Blue)
                        const denominator = (g + r - b) === 0 ? 0.0001 : (g + r - b);
                        const vari = (g - r) / denominator;

                        // Restrict bounds of VARI to sensible values (-1 to +1)
                        if (vari > -2 && vari < 2) {
                            totalVARI += vari;
                            validPixels++;
                        }
                    }

                    if (validPixels === 0) return resolve(null);

                    const avgVari = totalVARI / validPixels;
                    // Mapped to an NDVI scale approximation. 
                    // VARI correlates positively with vegetation density.
                    let proxyNDVI = Math.max(-1.0, Math.min(1.0, avgVari * 3.5));

                    resolve(proxyNDVI);
                };

                img.onerror = () => {
                    console.error("[CANOPY VARI] Failed to fetch proxy tile. Cannot compute live pixels.");
                    resolve(null);
                };
            } catch (err) {
                console.error("[CANOPY VARI] Exception in pixel loop: ", err);
                resolve(null);
            }
        });
    }
}
window.CanopyVARI = CanopyVARI;
