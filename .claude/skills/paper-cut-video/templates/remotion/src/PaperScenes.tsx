import React from 'react';
import {
  AbsoluteFill,
  Img,
  interpolate,
  OffthreadVideo,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

const RED = '#a92e22';
const RED_DARK = '#6f1915';
const INK = '#241d18';
const PAPER = '#f1e4c7';
const OCHRE = '#b18445';
const BLUE = '#78a8b8';
const GREEN = '#7ca77c';
const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const paperShadow = '16px 18px 0 rgba(52,25,16,.18), 0 5px 20px rgba(52,25,16,.12)';

const pop = (frame: number, at: number, fps: number) =>
  spring({frame: frame - at, fps, config: {damping: 16, stiffness: 170, mass: 0.7}});

const fade = (frame: number, at: number, length = 12) =>
  interpolate(frame, [at, at + length], [0, 1], clamp);

const isVideo = (src: string) => /\.(?:mp4|mov|m4v|webm)$/i.test(src);

const Media: React.FC<{src: string; style?: React.CSSProperties}> = ({src, style}) => {
  const resolved = staticFile(src);
  return isVideo(src)
    ? <OffthreadVideo src={resolved} muted style={style} />
    : <Img src={resolved} style={style} />;
};

const PaperBackground: React.FC = () => (
  <AbsoluteFill style={{backgroundColor: '#dbc49d'}}>
    <Img src={staticFile('assets/paper-bg-vertical.png')} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
    <AbsoluteFill
      style={{
        boxShadow: 'inset 0 0 110px rgba(52,24,16,.24)',
        background: 'radial-gradient(circle at 20% 30%, rgba(70,43,25,.07) 0 1px, transparent 2px), radial-gradient(circle at 75% 62%, rgba(70,43,25,.05) 0 1px, transparent 2px)',
        backgroundSize: '13px 13px, 17px 17px',
        opacity: 0.35,
      }}
    />
  </AbsoluteFill>
);

const Header: React.FC<{chapter: string}> = ({chapter}) => (
  <>
    <div
      style={{
        position: 'absolute', left: 46, top: 38,
        fontFamily: 'Arial, sans-serif', fontSize: 18, fontWeight: 800,
        letterSpacing: 3, color: 'rgba(36,29,24,.5)',
      }}
    >
      PAPER CUT · {chapter}
    </div>
    <div style={{position: 'absolute', left: 54, top: 100, width: 180, height: 16, background: RED, opacity: 0.92}} />
    <div style={{position: 'absolute', left: 246, top: 106, width: 780, height: 3, background: RED_DARK, opacity: 0.38}} />
  </>
);

const TornCard: React.FC<{children: React.ReactNode; style?: React.CSSProperties; accent?: string}> = ({
  children,
  style,
  accent = RED,
}) => (
  <div
    style={{
      backgroundColor: PAPER,
      border: '2px solid rgba(59,38,25,.45)',
      boxShadow: paperShadow,
      clipPath: 'polygon(2% 0, 98% 2%, 100% 92%, 96% 100%, 1% 97%, 0 8%)',
      color: INK,
      overflow: 'hidden',
      ...style,
    }}
  >
    <div style={{position: 'absolute', left: 0, top: 0, bottom: 0, width: 8, background: accent, opacity: 0.9}} />
    {children}
  </div>
);

const Placeholder: React.FC<{label: string}> = ({label}) => (
  <div
    style={{
      width: '100%', height: '100%', display: 'grid', placeItems: 'center',
      background: 'linear-gradient(135deg, rgba(255,255,255,.94), rgba(236,226,202,.96))',
      color: 'rgba(36,29,24,.48)', fontFamily: 'Menlo, monospace', fontWeight: 800,
      fontSize: 26, letterSpacing: 2, textAlign: 'center', whiteSpace: 'pre-line',
    }}
  >
    {label}
  </div>
);

export type PaperExplainerProps = {
  chapter: string;
  screenSrc?: string;
  presenterSrc?: string;
  supportTitle: string;
  supportCode?: string;
  supportSteps: string[];
  caption?: string;
};

export const PaperExplainer: React.FC<PaperExplainerProps> = ({
  chapter,
  screenSrc,
  presenterSrc,
  supportTitle,
  supportCode,
  supportSteps,
  caption,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const screen = pop(frame, 4, fps);
  const support = pop(frame, 28, fps);
  const pip = pop(frame, 12, fps);

  return (
    <AbsoluteFill>
      <PaperBackground />
      <Header chapter={chapter} />

      <div
        style={{
          position: 'absolute', left: 36, top: 170, width: 1008, height: 820,
          padding: 14, background: PAPER, border: `6px solid ${RED_DARK}`,
          boxShadow: paperShadow,
          opacity: screen,
          transform: `translateY(${interpolate(screen, [0, 1], [-44, 0])}px) rotate(${interpolate(screen, [0, 1], [-1.5, 0])}deg)`,
        }}
      >
        <div style={{width: '100%', height: '100%', overflow: 'hidden', background: '#fff'}}>
          {screenSrc
            ? <Media src={screenSrc} style={{width: '100%', height: '100%', objectFit: 'contain'}} />
            : <Placeholder label={'SCREEN RECORDING\n仅保留应用窗口'} />}
        </div>
      </div>

      <TornCard
        accent={BLUE}
        style={{
          position: 'absolute', left: 70, top: 1050, width: 600, minHeight: 230,
          padding: '34px 38px 30px 48px', opacity: support,
          transform: `translateX(${interpolate(support, [0, 1], [-55, 0])}px) rotate(-1deg)`,
        }}
      >
        <div style={{fontFamily: 'Arial, sans-serif', fontSize: 18, fontWeight: 900, letterSpacing: 4, color: RED}}>
          CONTEXT CARD
        </div>
        <div style={{marginTop: 12, fontFamily: '"Songti SC", STSong, serif', fontSize: 46, fontWeight: 900}}>
          {supportTitle}
        </div>
        {supportCode ? (
          <div
            style={{
              display: 'inline-block', marginTop: 16, padding: '9px 16px',
              background: INK, color: PAPER, fontFamily: 'Menlo, monospace',
              fontSize: 27, fontWeight: 800, borderRadius: 6,
            }}
          >
            {supportCode}
          </div>
        ) : null}
        <div style={{display: 'flex', alignItems: 'center', gap: 6, marginTop: 20, flexWrap: 'wrap'}}>
          {supportSteps.slice(0, 3).map((step, index) => {
            const stepPop = pop(frame, 42 + index * 10, fps);
            return (
              <React.Fragment key={step}>
                <div
                  style={{
                    padding: '6px 8px', background: index === supportSteps.length - 1 ? '#d8e1c9' : '#ead9bd',
                    border: '2px solid rgba(59,38,25,.35)', fontFamily: '"Songti SC", STSong, serif',
                    fontSize: 21, fontWeight: 800, opacity: stepPop,
                    transform: `translateY(${interpolate(stepPop, [0, 1], [18, 0])}px)`,
                  }}
                >
                  {step}
                </div>
                {index < Math.min(2, supportSteps.length - 1) ? <div style={{fontSize: 20, color: RED_DARK}}>→</div> : null}
              </React.Fragment>
            );
          })}
        </div>
      </TornCard>

      <div
        style={{
          position: 'absolute', left: 680, top: 1300, width: 340, height: 340,
          borderRadius: '50%', overflow: 'hidden', background: PAPER,
          border: `12px solid ${PAPER}`, outline: `4px solid ${RED_DARK}`,
          boxShadow: '12px 14px 0 rgba(52,25,16,.18), 0 8px 20px rgba(52,25,16,.18)',
          opacity: pip,
          transform: `scale(${interpolate(pip, [0, 1], [.75, 1])}) rotate(${interpolate(pip, [0, 1], [4, 0])}deg)`,
        }}
      >
        {presenterSrc
          ? <Media src={presenterSrc} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
          : <Placeholder label={'PRESENTER\n圆形画中画'} />}
      </div>

      {caption ? (
        <div
          style={{
            position: 'absolute', left: 70, right: 70, bottom: 128,
            display: 'flex', justifyContent: 'center', textAlign: 'center',
            fontFamily: '"Heiti SC", STHeiti, sans-serif', fontSize: 58,
            lineHeight: 1.25, fontWeight: 900, color: '#f7f1e7',
          }}
        >
          <span style={{padding: '15px 26px', background: 'rgba(24,19,18,.92)', borderRadius: 18, boxShadow: '0 8px 18px rgba(24,19,18,.2)'}}>
            {caption}
          </span>
        </div>
      ) : null}
    </AbsoluteFill>
  );
};

export type PaperCharacterAsset = {
  src?: string;
  label: string;
  layer: 'rear' | 'hero' | 'foreground';
  left: number;
  top: number;
  width: number;
  at: number;
  enterFrom?: 'left' | 'right' | 'up' | 'down';
  rotate?: number;
  opacity?: number;
};

export type PaperCharacterSceneProps = {
  chapter: string;
  title: string;
  backgroundSrc?: string;
  characters: PaperCharacterAsset[];
  caption?: string;
};

const PaperFigurePlaceholder: React.FC<{label: string; layer: PaperCharacterAsset['layer']}> = ({label, layer}) => {
  const color = layer === 'hero' ? RED : layer === 'foreground' ? OCHRE : BLUE;
  const armRotation = layer === 'hero' ? -24 : layer === 'foreground' ? 24 : -8;
  return (
    <div style={{position: 'relative', width: '100%', aspectRatio: '0.58', filter: 'drop-shadow(12px 15px 6px rgba(45,22,15,.24))'}}>
      <div
        style={{
          position: 'absolute', left: '33%', top: '2%', width: '34%', height: '17%',
          borderRadius: '50% 50% 42% 42%', background: INK, border: `6px solid ${PAPER}`,
          transform: 'rotate(-3deg)', zIndex: 2,
        }}
      />
      <div
        style={{
          position: 'absolute', left: '31%', top: '5%', width: '38%', aspectRatio: '1',
          borderRadius: '48% 52% 46% 54%', background: PAPER, border: `8px solid ${color}`,
          boxShadow: `inset 0 0 0 3px ${INK}`, zIndex: 3,
        }}
      >
        <div style={{position: 'absolute', left: '24%', top: '42%', width: 10, height: 10, borderRadius: '50%', background: INK}} />
        <div style={{position: 'absolute', right: '24%', top: '42%', width: 10, height: 10, borderRadius: '50%', background: INK}} />
        <div style={{position: 'absolute', left: '34%', right: '34%', bottom: '23%', height: 4, background: INK, transform: 'rotate(4deg)'}} />
      </div>
      <div
        style={{
          position: 'absolute', left: '20%', right: '20%', top: '24%', height: '49%',
          clipPath: 'polygon(25% 0, 75% 0, 100% 24%, 84% 100%, 16% 100%, 0 24%)',
          background: `linear-gradient(135deg, ${color}, ${PAPER} 86%)`,
          border: `7px solid ${PAPER}`, boxShadow: `inset 0 0 0 3px ${INK}`, zIndex: 2,
        }}
      />
      <div style={{position: 'absolute', left: '8%', top: '31%', width: '30%', height: '12%', borderRadius: 999, background: color, border: `6px solid ${PAPER}`, transformOrigin: 'right center', transform: `rotate(${armRotation}deg)`, zIndex: 1}} />
      <div style={{position: 'absolute', right: '8%', top: '31%', width: '30%', height: '12%', borderRadius: 999, background: color, border: `6px solid ${PAPER}`, transformOrigin: 'left center', transform: `rotate(${-armRotation}deg)`, zIndex: 1}} />
      <div style={{position: 'absolute', left: '29%', top: '68%', width: '18%', height: '23%', background: PAPER, border: `6px solid ${color}`, transform: 'rotate(3deg)', zIndex: 1}} />
      <div style={{position: 'absolute', right: '29%', top: '68%', width: '18%', height: '23%', background: PAPER, border: `6px solid ${color}`, transform: 'rotate(-3deg)', zIndex: 1}} />
      <div
        style={{
          position: 'absolute', left: '8%', right: '8%', bottom: 0, padding: '12px 10px',
          background: PAPER, border: `3px solid ${INK}`, color: INK, zIndex: 4,
          fontFamily: '"Songti SC", STSong, serif', fontSize: 28, lineHeight: 1.1,
          fontWeight: 900, textAlign: 'center', transform: 'rotate(-1deg)',
        }}
      >{label}</div>
    </div>
  );
};

const LayeredCharacter: React.FC<{asset: PaperCharacterAsset; index: number}> = ({asset, index}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const p = pop(frame, asset.at, fps);
  const travel = asset.layer === 'hero' ? 86 : asset.layer === 'foreground' ? 54 : 26;
  const startScale = asset.layer === 'hero' ? 0.88 : asset.layer === 'foreground' ? 0.93 : 0.97;
  const idleAmount = asset.layer === 'hero' ? 4 : asset.layer === 'foreground' ? 5 : 2;
  const enterFrom = asset.enterFrom ?? (asset.layer === 'hero' ? 'down' : index % 2 ? 'right' : 'left');
  const startX = enterFrom === 'left' ? -travel : enterFrom === 'right' ? travel : 0;
  const startY = enterFrom === 'up' ? -travel : enterFrom === 'down' ? travel : 0;
  const x = interpolate(p, [0, 1], [startX, 0]);
  const y = interpolate(p, [0, 1], [startY, 0]);
  const idle = frame < asset.at ? 0 : Math.sin((frame - asset.at) / 18 + index * 1.7) * idleAmount * p;
  const zIndex = asset.layer === 'hero' ? 40 : asset.layer === 'foreground' ? 60 : 20;

  return (
    <div
      style={{
        position: 'absolute', left: asset.left, top: asset.top, width: asset.width,
        zIndex, opacity: p * (asset.opacity ?? 1), transformOrigin: 'bottom center',
        transform: `translate3d(${x}px, ${y + idle}px, 0) scale(${interpolate(p, [0, 1], [startScale, 1])}) rotate(${interpolate(p, [0, 1], [(asset.rotate ?? 0) + (enterFrom === 'left' ? -3 : 3), asset.rotate ?? 0])}deg)`,
      }}
    >
      {asset.src ? (
        <Media
          src={asset.src}
          style={{
            width: '100%', height: 'auto', objectFit: 'contain',
            filter: 'drop-shadow(5px 0 0 #f7ead0) drop-shadow(-5px 0 0 #f7ead0) drop-shadow(0 5px 0 #f7ead0) drop-shadow(12px 15px 6px rgba(45,22,15,.26))',
          }}
        />
      ) : <PaperFigurePlaceholder label={asset.label} layer={asset.layer} />}
    </div>
  );
};

export const PaperCharacterScene: React.FC<PaperCharacterSceneProps> = ({
  chapter,
  title,
  backgroundSrc,
  characters,
  caption,
}) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const heading = pop(frame, 4, fps);
  const backgroundDrift = interpolate(frame, [0, durationInFrames], [0, -14], clamp);

  return (
    <AbsoluteFill style={{overflow: 'hidden', background: '#dbc49d'}}>
      {backgroundSrc ? (
        <AbsoluteFill style={{transform: `translateX(${backgroundDrift}px) scale(1.015)`}}>
          <Media src={backgroundSrc} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
          <AbsoluteFill style={{boxShadow: 'inset 0 0 110px rgba(52,24,16,.2)'}} />
        </AbsoluteFill>
      ) : <PaperBackground />}

      <Header chapter={chapter} />
      <TornCard
        style={{
          position: 'absolute', left: 64, top: 146, width: 700, minHeight: 130,
          padding: '27px 36px 24px 46px', zIndex: 80, opacity: heading,
          transform: `translateY(${interpolate(heading, [0, 1], [-34, 0])}px) rotate(-1deg)`,
        }}
      >
        <div style={{fontFamily: '"Songti SC", STSong, serif', fontSize: 54, lineHeight: 1.12, fontWeight: 900}}>{title}</div>
      </TornCard>

      {characters.map((asset, index) => <LayeredCharacter key={`${asset.label}-${index}`} asset={asset} index={index} />)}

      {caption ? (
        <div
          style={{
            position: 'absolute', left: 70, right: 70, bottom: 128, zIndex: 100,
            display: 'flex', justifyContent: 'center', textAlign: 'center',
            fontFamily: '"Heiti SC", STHeiti, sans-serif', fontSize: 58,
            lineHeight: 1.25, fontWeight: 900, color: '#f7f1e7',
          }}
        >
          <span style={{padding: '15px 26px', background: 'rgba(24,19,18,.92)', borderRadius: 18, boxShadow: '0 8px 18px rgba(24,19,18,.2)'}}>
            {caption}
          </span>
        </div>
      ) : null}
    </AbsoluteFill>
  );
};

const FlowNode: React.FC<{title: string; sub: string; y: number; at: number; accent: string}> = ({title, sub, y, at, accent}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const p = pop(frame, at, fps);
  return (
    <TornCard
      accent={accent}
      style={{
        position: 'absolute', left: 180, top: y, width: 720, height: 210,
        padding: '38px 42px 30px 52px', opacity: p,
        transform: `translateY(${interpolate(p, [0, 1], [48, 0])}px) scale(${interpolate(p, [0, 1], [.92, 1])})`,
      }}
    >
      <div style={{fontFamily: '"Songti SC", STSong, serif', fontSize: 48, lineHeight: 1.15, fontWeight: 900, textAlign: 'center'}}>
        {title}
      </div>
      <div style={{marginTop: 15, fontFamily: 'Menlo, monospace', fontSize: 22, color: 'rgba(36,29,24,.65)', textAlign: 'center'}}>
        {sub}
      </div>
    </TornCard>
  );
};

const Arrow: React.FC<{y: number; at: number}> = ({y, at}) => {
  const frame = useCurrentFrame();
  const p = fade(frame, at, 14);
  return (
    <div style={{position: 'absolute', left: 538, top: y, width: 4, height: 105, background: INK, transformOrigin: 'top', transform: `scaleY(${p})`}}>
      <div style={{position: 'absolute', left: -9, bottom: -2, width: 0, height: 0, borderLeft: '11px solid transparent', borderRight: '11px solid transparent', borderTop: `18px solid ${INK}`}} />
    </div>
  );
};

export const PaperFlow: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const title = pop(frame, 4, fps);
  return (
    <AbsoluteFill>
      <PaperBackground />
      <Header chapter="PROGRESSIVE FLOW" />
      <div style={{position: 'absolute', left: 70, right: 70, top: 150, textAlign: 'center', opacity: title, transform: `translateY(${interpolate(title, [0, 1], [-36, 0])}px)`}}>
        <div style={{fontFamily: '"Songti SC", STSong, serif', fontSize: 74, fontWeight: 900}}>渐进式讲解流程</div>
        <div style={{marginTop: 12, fontFamily: 'Arial, sans-serif', fontSize: 20, letterSpacing: 4, color: RED}}>ONE IDEA AT A TIME</div>
      </div>
      <FlowNode title="第一层：先给结论" sub="一句话建立整体认知" y={390} at={25} accent={BLUE} />
      <Arrow y={605} at={58} />
      <FlowNode title="第二层：展开关键步骤" sub="只显示正在讲的节点" y={725} at={78} accent="#b68bab" />
      <Arrow y={940} at={112} />
      <FlowNode title="第三层：按需展示细节" sub="命令 · 路径 · 文件 · 示例" y={1060} at={132} accent={GREEN} />
      <div
        style={{
          position: 'absolute', left: 690, top: 1430, width: 280, height: 150,
          display: 'grid', placeItems: 'center', whiteSpace: 'pre-line',
          color: RED, border: `4px solid ${RED}`, boxShadow: `inset 0 0 0 6px ${PAPER}, inset 0 0 0 8px ${RED}`,
          fontFamily: '"Songti SC", STSong, serif', fontSize: 38, lineHeight: 1.2,
          fontWeight: 900, textAlign: 'center', opacity: pop(frame, 180, fps),
          transform: `rotate(-7deg) scale(${interpolate(pop(frame, 180, fps), [0, 1], [1.35, 1])})`,
        }}
      >
        {'用到哪\n讲到哪'}
      </div>
    </AbsoluteFill>
  );
};

export type PaperOutroProps = {
  creatorName: string;
  tagline: string;
  callToAction: string;
  presenterSrc?: string;
};

export const PaperOutro: React.FC<PaperOutroProps> = ({creatorName, tagline, callToAction, presenterSrc}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const card = pop(frame, 7, fps);
  const title = fade(frame, 24, 18);
  const sub = fade(frame, 42, 18);
  const stamp = pop(frame, 62, fps);
  const person = pop(frame, 12, fps);

  return (
    <AbsoluteFill>
      <PaperBackground />
      <Header chapter="FOLLOW FOR MORE" />
      <div style={{position: 'absolute', left: -95, top: 150, fontFamily: 'Georgia, serif', fontSize: 520, lineHeight: 1, fontWeight: 900, color: 'rgba(169,46,34,.075)', transform: 'rotate(-8deg)'}}>AI</div>

      <div
        style={{
          position: 'absolute', left: 40, top: 870, width: 600, height: 700,
          opacity: person, transform: `translateX(${interpolate(person, [0, 1], [-70, 0])}px) rotate(-2deg)`,
          filter: 'drop-shadow(15px 18px 7px rgba(45,22,15,.22))',
        }}
      >
        {presenterSrc
          ? <Media src={presenterSrc} style={{width: '100%', height: '100%', objectFit: 'contain'}} />
          : (
            <div style={{width: 470, height: 610, margin: '30px auto', display: 'grid', placeItems: 'center', background: '#d7c09a', border: `8px solid ${PAPER}`, clipPath: 'polygon(8% 0, 91% 3%, 100% 88%, 86% 100%, 5% 96%, 0 12%)', color: 'rgba(36,29,24,.52)', fontFamily: 'Menlo, monospace', fontSize: 25, fontWeight: 800, textAlign: 'center', whiteSpace: 'pre-line'}}>
              {'PAPER PRESENTER\n透明人物剪纸'}
            </div>
          )}
      </div>

      <TornCard
        style={{
          position: 'absolute', left: 300, right: 62, top: 320, height: 570,
          padding: '66px 52px 46px 72px', opacity: card,
          transform: `translateY(${interpolate(card, [0, 1], [-65, 0])}px) scale(${interpolate(card, [0, 1], [.94, 1])}) rotate(-1deg)`,
        }}
      >
        <div style={{fontFamily: 'Arial, sans-serif', fontSize: 23, fontWeight: 900, letterSpacing: 5, color: RED}}>THANKS FOR WATCHING</div>
        <div style={{marginTop: 34, fontFamily: '"Songti SC", STSong, serif', fontSize: 88, lineHeight: 1.08, fontWeight: 900, letterSpacing: -4, opacity: title}}>
          我是<br /><span style={{color: RED}}>{creatorName}</span>
        </div>
        <div style={{marginTop: 35, paddingTop: 26, borderTop: `3px solid ${OCHRE}`, fontFamily: '"Songti SC", STSong, serif', fontSize: 37, lineHeight: 1.42, fontWeight: 800, color: INK, opacity: sub}}>
          {tagline}
        </div>
      </TornCard>

      <div
        style={{
          position: 'absolute', right: 96, bottom: 210, width: 285, height: 172,
          display: 'grid', placeItems: 'center', whiteSpace: 'pre-line',
          color: RED, border: `4px solid ${RED}`, boxShadow: `inset 0 0 0 6px ${PAPER}, inset 0 0 0 8px ${RED}`,
          fontFamily: '"Songti SC", STSong, serif', fontSize: 48, lineHeight: 1.2,
          fontWeight: 900, textAlign: 'center', opacity: stamp,
          transform: `scale(${interpolate(stamp, [0, 1], [1.28, 1])}) rotate(-8deg)`,
        }}
      >
        {callToAction}
      </div>
    </AbsoluteFill>
  );
};
