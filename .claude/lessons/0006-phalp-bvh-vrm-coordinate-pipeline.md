---
id: 0006
slug: phalp-bvh-vrm-coordinate-pipeline
title: PHALP → BVH → VRMA → VRM 跨階段座標系與 rig 陷阱
date: 2026-04-12
tags: [frontend, three-vrm, bvh2vrma, coordinate, phase2]
---

## 錯誤是什麼

Phase 2 把 Phase 1 輸出的 dance.bvh 在瀏覽器透過 bvh2vrma 轉成 VRMA 並套到 VRM 上播放時，連續踩了 4 個不同座標系 / rig 層級的地雷：

1. **角色背對相機**：VRM 顯示時預設背對。
2. **上下顛倒**：載入動畫後角色頭下腳上。
3. **沉入地面**：動畫一開始角色就沉到地面下，地平面落在肩膀高度。
4. **完全不動**：試圖修掉沉地面後整個 mixer 不動了。

## 為什麼犯

整條 pipeline 跨 4 個不同的座標 / rig 約定，**任何一階沒對齊都會出問題**，而每個階的錯誤長得像是別階的錯誤：

### 1. PHALP 的 `global_orient` 是相機座標 (Y down, Z forward)

PHALP / 4D-Humans 的姿態預測輸出的 `smpl[i]['global_orient']` 是把 SMPL canonical body 轉到 **OpenCV 相機座標** 的 rotation matrix。OpenCV 相機：

- X right
- **Y down**
- **Z forward (into scene)**

而 VRM / three.js 世界是：
- X right
- **Y up**
- **Z out of screen (toward viewer)**

smpl2bvh 只是把 rotation matrix 轉成 axis-angle 再寫進 BVH，**完全不做座標轉換**，因此 BVH 裡的 root rotation 是相機座標的。直接餵給 VRM 會上下顛倒加背對。

**正解**：在 `extract_longest_track` 對 root (global_orient) 左乘座標變換矩陣：

```python
_R_CAM_TO_VRM = np.diag([1.0, -1.0, -1.0]).astype(np.float32)
# ...
go = _R_CAM_TO_VRM @ go  # root only; body_pose 是 local rotation 不用轉
```

只轉 root 就好，body_pose 是子骨相對 parent 的 local rotation，跟世界座標無關。

### 2. VRM1 rest pose 面向 +Z，但 three.js 相機通常在 +Z 往 -Z 看

VRM1 規格：rest pose 角色面向 **+Z**。three.js 預設相機放在 +Z 位置往原點看（forward = -Z）。所以 VRM 角色背對相機是**預期行為**，不是你做錯。

要讓角色面對相機，在 VrmPreview 裡：

```ts
vrm.scene.rotation.y = Math.PI;  // 繞 Y 軸 180° 轉正面
```

**不要在 scene root 下 rotation.x**：那會把 Y 軸翻掉再順便把 Z 翻掉，跟 1. 的 root rotation 疊起來結果很奇怪。

### 3. bvh2vrma 的 hipsPositionTrack 會把 VRM hips 拉到原點

bvh2vrma 原始碼在 `convertBVHToVRMAnimation.ts` 對 hips position track 做了這件事：

```ts
if (hipsPositionTrack != null) {
  const offset = hipsBone.position.toArray();
  for (let i = 0; i < hipsPositionTrack.values.length; i++) {
    hipsPositionTrack.values[i] -= offset[i % 3];  // 減掉 rest offset
  }
}
```

對於 `smpl_trans` 全 0 的 BVH（我們 Phase 1 沒有 root translation），這樣處理完 **hipsPositionTrack 的值全是 0**。

這個 track 透過 VRMAnimationExporterPlugin 寫進 glb 的 VRMC_vrm_animation extension。在播放端 `@pixiv/three-vrm-animation` 的 `createVRMAnimationClip` 會把它變成一條 `Normalized_Hips.position` keyframe track。然後 AnimationMixer 每一 frame 都把 `Normalized_Hips.position = (0, 0, 0)`。

接下來 `vrm.update(dt)` → `humanoid.update()` → `VRMHumanoidRig.update()` 對 hips 有特殊處理（`three-vrm-core` line ~1960）：

```js
if (boneName === 'hips') {
  const boneWorldPosition = rigBoneNode.getWorldPosition(_boneWorldPos);
  // ... 把 normalized rig hips 的 world position 複製到 raw hips 的 local position
}
```

它把 normalized rig hips 的 world position **強制拷貝**到 raw VRM hips 的 local position。Normalized_Hips 被 mixer 寫成 local (0,0,0)，它的 parent (VRMHumanoidRig root) 又在 (0,0,0)，所以 hips world = (0,0,0)，raw VRM hips 也跟著被拉到原點 → 整個角色沉下去。

**正解**：在我們 vendored 的 `convertBVHToVRMAnimation.ts` 完全不輸出 hipsPositionTrack，讓 mixer 不碰 Normalized_Hips.position，VRM hips 留在自己 rest 位置。代價是所有 root translation（跑動、跳躍）都被丟掉，但 Phase 1 本來就沒算 translation，沒損失。

### 4. 拿掉 hipsPositionTrack 後仍需保留 auto-grounding

bvh2vrma 原本還有一段：

```ts
const boundingBox = createSkeletonBoundingBox(skeleton);
if (boundingBox.min.y < 0) {
  rootBone.position.y -= boundingBox.min.y;
}
```

我們的 BVH 是從 SMPL canonical rest pose 產生的，pelvis 初始 Y ≈ -22 cm，腳底 Y ≈ -110 cm。scale 0.01 後 min.y ≈ -1.1 m。Auto-grounding 把 rootBone 整個抬 1.1 m，讓 min.y 對齊 0。

**我一度以為拿掉 hipsPositionTrack 後這段也可以拿掉**——畢竟它只改 rootBone.position，不影響 rotation track 的內容。但是會讓整個 clip 完全不動。

**根因推測**：exported glb 的 hips rest world Y 是負值 → `VRMAnimationLoaderPlugin` 讀 `restHipsPosition.y = -0.22` → `createVRMAnimationHumanoidTracks` 算 `scale = humanoidY / animationY = positive / negative = 負值` → 雖然我們沒有 translation track 應該不會用到這個 scale，但某處（可能是 PropertyBinding 的初始化、或者 mixer 對含 NaN/負值 rest 的不良處理）會讓整組 binding 失敗，mixer.update 看起來在跑但實際沒把值寫到 Normalized_ 任何骨頭上。

**正解**：保留 auto-grounding，但拿掉 hipsPositionTrack。兩者分工明確：
- Auto-grounding：讓 exported glb 的 rest skeleton bbox min.y = 0，rest hips Y 是正值
- 不輸出 hipsPositionTrack：讓 VRM hips 動畫過程中停在自己原生的 rest 位置

## 未來如何避免

### debug 方法論

跨階段 pipeline 的座標問題要按順序定位錯在哪一階，而不是亂 rotate 試錯：

1. **先用 matplotlib / GIF 驗證 SMPL 關節 3D 位置**（Phase 1 的 `render_skeleton_gif`）——確認 PHALP → SMPL 解碼正確
2. **用 2D overlay 驗證投影**（`render_overlay_video`）——確認 joints 與原影片對齊
3. **BVH 用 Blender 打開驗證骨架命名**（Phase 1.7）——確認 BVH 層級 OK
4. **VRMA 套上 VRM 前先印出 clip.tracks 的數量與名字**——確認 bvh2vrma 轉換 + VRMAnimationLoaderPlugin 解析 OK
5. **印出 `vrm.scene.getObjectByName('Normalized_Hips')`**——確認 mixer 綁定目標存在
6. **每條 track 的前幾個 quaternion 值**——確認值不是 identity / NaN

看到 "角色不動" 先用 6 的方法分辨是 binding 掛了還是值全是 identity。

### useEffect / state 規則

載入異步資源（VRM 52 MB）的 React 元件，**要把載入完成的物件放進 state 而不是只用 ref**。useEffect 依賴的 ref 不會觸發 rerun，使用者只要在資源載入前操作就會錯過綁定時機。

pattern：

```ts
const vrmRef = useRef<VRM | null>(null);  // 給 tick 用（tick 是 closure 抓不到 state）
const [vrm, setVrm] = useState<VRM | null>(null);  // 給 effect 用

useEffect(() => {
  loader.load(url, (gltf) => {
    vrmRef.current = gltf.userData.vrm;
    setVrm(gltf.userData.vrm);
  });
}, [url]);

useEffect(() => {
  if (!vrm || !vrmaBlob) return;  // 等兩個都到
  // 建 mixer, 綁 clip
}, [vrm, vrmaBlob]);
```

### three-vrm rig 系統要點

- `vrm.humanoid.getNormalizedBoneNode(name)` 回傳的是 `Normalized_<原 bone name>`，**不是原 bone**
- 動畫 clip 的 track name 也是 `Normalized_<Name>.quaternion` / `.position`
- 這些 Normalized_ 節點掛在 `VRMHumanoidRig` root 下，加在 `vrm.scene` 裡，用 `scene.getObjectByName` 找得到
- `vrm.update(dt)` 必須每 frame 呼叫才會把 normalized pose 套到 raw skeleton，**不呼叫的話 mixer 就算有寫值也看不到**
- `VRMHumanoidRig.update()` 對 hips 的特殊處理會把 rig hips world position 強拷到 raw hips local position——所以任何會動到 `Normalized_Hips.position` 的 track 都會影響 raw 角色位置

## 如何判斷是否適用

- 任何時候做 PHALP / HMR / SPIN / VIBE → BVH → VRM 系列 pipeline
- 任何時候 BVH 的 root rotation 是從 camera-frame 姿態估計器來的
- 任何時候用 bvh2vrma / 類似工具把 BVH 轉 VRMA
- 任何時候 AnimationMixer 看起來沒效果但 console 沒 error
- 任何時候載入 VRM 的 React 元件動畫掛不上去

## 參考檔案

- `backend/app/services/smpl_to_bvh_service.py` line ~30：`_R_CAM_TO_VRM` 的定義與套用
- `frontend/src/components/VrmPreview.tsx`：VRM state + ref 雙軌、rotation.y = Math.PI
- `frontend/src/lib/bvh2vrma/convertBVHToVRMAnimation.ts`：拿掉 hipsPositionTrack 但保留 auto-grounding
- `node_modules/@pixiv/three-vrm-core/lib/three-vrm-core.module.js` line ~1952：`VRMHumanoidRig.update()` 對 hips 的特殊處理
- `node_modules/@pixiv/three-vrm-animation/lib/three-vrm-animation.module.js` line ~436：`createVRMAnimationHumanoidTracks`
