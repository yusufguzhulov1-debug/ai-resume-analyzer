import React from 'react';
import {Composition} from 'remotion';
import {
  PaperCharacterScene,
  PaperCharacterSceneProps,
  PaperExplainer,
  PaperExplainerProps,
  PaperFlow,
  PaperOutro,
  PaperOutroProps,
} from './PaperScenes';

const characterDefaults: PaperCharacterSceneProps = {
  chapter: 'CHARACTER FIRST',
  title: '人物要为这句话行动',
  characters: [
    {label: '后排伙伴', layer: 'rear', left: 72, top: 890, width: 260, at: 36, enterFrom: 'left', rotate: -3, opacity: 0.78},
    {label: '讲解主角', layer: 'hero', left: 286, top: 500, width: 510, at: 10, enterFrom: 'down'},
    {label: '前景角色', layer: 'foreground', left: 748, top: 1020, width: 300, at: 54, enterFrom: 'right', rotate: 3},
  ],
  caption: '先按文案设计人物和场景，再开始动画。',
};

const explainerDefaults: PaperExplainerProps = {
  chapter: 'SCREEN + CONTEXT',
  supportTitle: '当前操作',
  supportCode: '/skills',
  supportSteps: ['打开命令菜单', '选择目标 Skill', '读取并执行'],
  caption: '也就是咱们直接通过斜杠的方式调用。',
};

const outroDefaults: PaperOutroProps = {
  creatorName: '你的名字',
  tagline: '带你看懂更多 AI 工具',
  callToAction: '关注我\n下期见',
};

export const RemotionRoot: React.FC = () => (
  <>
    <Composition
      id="PaperCharacterScene"
      component={PaperCharacterScene}
      width={1080}
      height={1920}
      fps={30}
      durationInFrames={240}
      defaultProps={characterDefaults}
    />
    <Composition
      id="PaperExplainer"
      component={PaperExplainer}
      width={1080}
      height={1920}
      fps={30}
      durationInFrames={240}
      defaultProps={explainerDefaults}
    />
    <Composition id="PaperFlow" component={PaperFlow} width={1080} height={1920} fps={30} durationInFrames={300} />
    <Composition
      id="PaperOutro"
      component={PaperOutro}
      width={1080}
      height={1920}
      fps={30}
      durationInFrames={120}
      defaultProps={outroDefaults}
    />
  </>
);
