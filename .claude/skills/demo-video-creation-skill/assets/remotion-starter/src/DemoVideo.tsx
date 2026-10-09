import React from "react";
import {
  AbsoluteFill,
  Img,
  Sequence,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  Easing,
} from "remotion";
import {demoConfig} from "./demoConfig";

const second = (value: number) => Math.round(value * 30);

const progress = (frame: number, start: number, end: number) =>
  interpolate(frame, [start, end], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.bezier(0.16, 1, 0.3, 1),
  });

const Shell: React.FC<{children: React.ReactNode; deep?: boolean}> = ({children, deep}) => (
  <AbsoluteFill
    style={{
      background: deep
        ? `linear-gradient(135deg, ${demoConfig.colors.ink}, #10223f)`
        : `linear-gradient(135deg, ${demoConfig.colors.background}, #ffffff)`,
      color: deep ? "#fff" : demoConfig.colors.ink,
      fontFamily: 'Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
      overflow: "hidden",
    }}
  >
    <div
      style={{
        position: "absolute",
        inset: 0,
        backgroundImage:
          "linear-gradient(rgba(37,99,235,0.08) 1px, transparent 1px), linear-gradient(90deg, rgba(37,99,235,0.08) 1px, transparent 1px)",
        backgroundSize: "72px 72px",
        opacity: deep ? 0.2 : 0.55,
      }}
    />
    {children}
  </AbsoluteFill>
);

const ProductFrame: React.FC<{image?: string; label: string; scale?: number}> = ({image, label, scale = 1}) => {
  const frame = useCurrentFrame();
  const drift = Math.sin(frame / 90) * 5;
  return (
    <div
      style={{
        width: 1060,
        height: 620,
        borderRadius: 28,
        overflow: "hidden",
        background: "#fff",
        boxShadow: "0 38px 90px rgba(26,44,80,0.22)",
        border: "1px solid rgba(44,70,116,0.12)",
        transform: `translateY(${drift}px) scale(${scale})`,
      }}
    >
      <div
        style={{
          height: 54,
          background: `linear-gradient(90deg, ${demoConfig.colors.primary}, ${demoConfig.colors.secondary})`,
          color: "#fff",
          display: "flex",
          alignItems: "center",
          padding: "0 24px",
          fontSize: 20,
          fontWeight: 700,
        }}
      >
        {demoConfig.productName}
        <div style={{marginLeft: "auto", opacity: 0.8, fontSize: 16}}>{label}</div>
      </div>
      {image ? (
        <Img src={staticFile(image)} style={{width: "100%", height: "calc(100% - 54px)", objectFit: "cover"}} />
      ) : (
        <div style={{padding: 42, height: "calc(100% - 54px)"}}>
          <div style={{height: 34, width: "52%", background: "#dfe8f8", borderRadius: 10, marginBottom: 28}} />
          <div style={{display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24}}>
            {[0, 1, 2, 3].map((item) => (
              <div key={item} style={{height: 170, borderRadius: 18, background: item === 1 ? "#e8fff7" : "#f0f4fb"}} />
            ))}
          </div>
          <div style={{height: 18, width: "78%", background: "#e8edf6", borderRadius: 9, marginTop: 28}} />
          <div style={{height: 18, width: "62%", background: "#e8edf6", borderRadius: 9, marginTop: 14}} />
        </div>
      )}
    </div>
  );
};

const Title: React.FC<{eyebrow?: string; headline: string; subline?: string; deep?: boolean}> = ({
  eyebrow,
  headline,
  subline,
  deep,
}) => {
  const frame = useCurrentFrame();
  const t = progress(frame, 4, 34);
  return (
    <div style={{transform: `translateY(${(1 - t) * 34}px)`, opacity: t}}>
      {eyebrow && (
        <div
          style={{
            color: demoConfig.colors.primary,
            fontWeight: 850,
            fontSize: 32,
            letterSpacing: 0,
            marginBottom: 26,
          }}
        >
          {eyebrow}
        </div>
      )}
      <div
        style={{
          fontFamily: 'Georgia, "Times New Roman", ui-serif, serif',
          fontSize: deep ? 122 : 112,
          lineHeight: 0.92,
          fontWeight: 800,
          maxWidth: 1050,
        }}
      >
        {headline}
      </div>
      {subline && (
        <div style={{fontSize: 35, lineHeight: 1.28, color: deep ? "rgba(255,255,255,0.76)" : demoConfig.colors.muted, maxWidth: 860, marginTop: 34}}>
          {subline}
        </div>
      )}
    </div>
  );
};

const HookScene: React.FC = () => (
  <Shell>
    <div style={{position: "absolute", left: 78, top: 88}}>
      <Title eyebrow={demoConfig.copy.eyebrow} headline={demoConfig.copy.headline} subline={demoConfig.copy.subline} />
    </div>
    <div style={{position: "absolute", right: 88, bottom: 110}}>
      <ProductFrame label="Live product" image={demoConfig.screenshots.setup} scale={0.82} />
    </div>
  </Shell>
);

const WorkflowScene: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const rail = spring({frame, fps, config: {damping: 18, stiffness: 70}});
  return (
    <Shell>
      <div style={{position: "absolute", left: 82, top: 112, width: 520}}>
        <Title headline={demoConfig.copy.setup} subline={demoConfig.copy.action} />
      </div>
      <div style={{position: "absolute", right: 90, top: 190}}>
        <ProductFrame label="Workflow" image={demoConfig.screenshots.action} scale={0.92 + rail * 0.04} />
      </div>
      <div
        style={{
          position: "absolute",
          left: 714 + rail * 550,
          top: 760 - rail * 300,
          width: 34,
          height: 34,
          borderRadius: 18,
          background: "#fff",
          border: `5px solid ${demoConfig.colors.primary}`,
          boxShadow: "0 10px 30px rgba(37,99,235,0.35)",
        }}
      />
    </Shell>
  );
};

const ResultScene: React.FC = () => {
  const frame = useCurrentFrame();
  const scan = progress(frame, 30, 100);
  return (
    <Shell deep>
      <div style={{position: "absolute", left: 86, top: 120}}>
        <Title headline={demoConfig.copy.result} subline="Use proof, comparison, or a visible output state." deep />
      </div>
      <div style={{position: "absolute", right: 92, top: 238}}>
        <ProductFrame label="Result" image={demoConfig.screenshots.result || demoConfig.screenshots.proof} scale={0.9} />
      </div>
      <div
        style={{
          position: "absolute",
          left: 760,
          right: 110,
          top: 250 + scan * 500,
          height: 5,
          background: `linear-gradient(90deg, transparent, ${demoConfig.colors.secondary}, transparent)`,
          boxShadow: `0 0 34px ${demoConfig.colors.secondary}`,
        }}
      />
    </Shell>
  );
};

const CtaScene: React.FC = () => (
  <Shell>
    <div style={{position: "absolute", left: 100, top: 154}}>
      <Title eyebrow={demoConfig.productName} headline={demoConfig.copy.cta} subline={demoConfig.url} />
    </div>
    <div
      style={{
        position: "absolute",
        right: 118,
        bottom: 132,
        padding: "28px 42px",
        borderRadius: 999,
        color: "#fff",
        background: `linear-gradient(90deg, ${demoConfig.colors.primary}, ${demoConfig.colors.secondary})`,
        fontSize: 34,
        fontWeight: 850,
        boxShadow: "0 30px 80px rgba(37,99,235,0.28)",
      }}
    >
      Start the demo
    </div>
  </Shell>
);

const TransitionOverlay: React.FC = () => {
  const frame = useCurrentFrame();
  const centers = [second(18), second(42), second(62)];
  return (
    <AbsoluteFill style={{pointerEvents: "none"}}>
      {centers.map((center, index) => {
        const t = progress(frame, center - 16, center + 26);
        const burst = Math.sin(t * Math.PI);
        if (t <= 0 || t >= 1) return null;
        return (
          <div
            key={center}
            style={{
              position: "absolute",
              left: `${index % 2 === 0 ? 62 : 28}%`,
              top: `${index % 2 === 0 ? 42 : 58}%`,
              width: 500 + t * 1800,
              height: 500 + t * 1800,
              marginLeft: -250 - t * 900,
              marginTop: -250 - t * 900,
              borderRadius: "50%",
              border: `8px solid rgba(37,99,235,${0.28 * burst})`,
              boxShadow: `0 0 ${120 * burst}px rgba(18,163,127,${0.34 * burst})`,
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};

export const ProductDemo: React.FC = () => (
  <>
    <Sequence from={0} durationInFrames={second(18)}>
      <HookScene />
    </Sequence>
    <Sequence from={second(18)} durationInFrames={second(24)}>
      <WorkflowScene />
    </Sequence>
    <Sequence from={second(42)} durationInFrames={second(20)}>
      <ResultScene />
    </Sequence>
    <Sequence from={second(62)} durationInFrames={second(13)}>
      <CtaScene />
    </Sequence>
    <TransitionOverlay />
  </>
);
