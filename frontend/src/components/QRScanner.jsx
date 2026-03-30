import { Html5Qrcode } from "html5-qrcode";
import { useEffect, useId, useRef, useState } from "react";

const QRScanner = ({ onScan, onError, isActive = true }) => {
  const scannerId = useId();
  const elementId = `qr-reader-${scannerId.replace(/:/g, "")}`;
  const hasScannedRef = useRef(false);
  const isRunningRef = useRef(false);
  const [cameraError, setCameraError] = useState("");

  useEffect(() => {
    if (!isActive) {
      return undefined;
    }

    let isMounted = true;
    hasScannedRef.current = false;

    const html5QrCode = new Html5Qrcode(elementId);

    html5QrCode
      .start(
        { facingMode: "environment" },
        { fps: 10, qrbox: { width: 260, height: 260 } },
        (decodedText) => {
          if (hasScannedRef.current) {
            return;
          }

          hasScannedRef.current = true;
          onScan(decodedText);

          if (isRunningRef.current) {
            html5QrCode
              .stop()
              .then(() => {
                isRunningRef.current = false;
                html5QrCode.clear();
              })
              .catch(() => undefined);
          }
        },
        () => undefined,
      )
      .then(() => {
        console.log("QR Scanner started");
        isRunningRef.current = true;
      })
      .catch((error) => {
        if (!isMounted) {
          return;
        }
        const message =
          typeof error === "string" ? error : "Unable to access camera";
        setCameraError(message);
        if (onError) {
          onError(message);
        }
      });

    return () => {
      isMounted = false;
      if (isRunningRef.current) {
        html5QrCode
          .stop()
          .then(() => {
            isRunningRef.current = false;
            html5QrCode.clear();
          })
          .catch(() => undefined);
      }
    };
  }, [elementId, isActive, onError, onScan]);


  return (
    <div className="space-y-3">
      <div
        id={elementId}
        className="mx-auto w-full max-w-sm overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm"
      />
      {cameraError ? (
        <p className="text-sm text-rose-600">{cameraError}</p>
      ) : (
        <p className="text-sm text-slate-500">
          Center the QR code inside the frame for instant check-in.
        </p>
      )}
    </div>
  );
};

export default QRScanner;
