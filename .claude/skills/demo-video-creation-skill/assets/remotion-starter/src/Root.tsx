import {Composition} from "remotion";
import {ProductDemo} from "./DemoVideo";

export const Root: React.FC = () => (
  <>
    <Composition
      id="ProductDemo"
      component={ProductDemo}
      durationInFrames={2250}
      fps={30}
      width={1920}
      height={1080}
    />
    <Composition
      id="ProductDemo4K"
      component={ProductDemo}
      durationInFrames={2250}
      fps={30}
      width={3840}
      height={2160}
    />
  </>
);
