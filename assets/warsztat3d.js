import * as T from './three-r180/three.module.min.js';
import { OrbitControls } from './three-r180/OrbitControls.js';
import { RoomEnvironment } from './three-r180/RoomEnvironment.js';
import { SimplexNoise } from './three-r180/SimplexNoise.js';

const cyan = 0x00e5ff;
const copper = 0xc37448;
const steel = 0x8e9ba3;
const turn = Math.PI * 2;
const vector = (x, y, z) => new T.Vector3(x, y, z);
const metal = (color, metalness = .85, roughness = .25) =>
  new T.MeshStandardMaterial({ color, metalness, roughness });
const glow = (color) => new T.MeshBasicMaterial({ color, toneMapped: false });

function mesh(parent, geometry, material, x = 0, y = 0, z = 0) {
  const object = new T.Mesh(geometry, material);
  object.position.set(x, y, z);
  parent.add(object);
  return object;
}

function box(parent, size, material, position) {
  return mesh(parent, new T.BoxGeometry(...size), material, ...position);
}

function cylinder(parent, radius, height, material, position, sides = 40) {
  return mesh(parent, new T.CylinderGeometry(radius, radius, height, sides), material, ...position);
}

function curve(points) {
  return new T.CatmullRomCurve3(points.map(p => vector(...p)));
}

function tube(parent, path, radius, material, segments = 42) {
  return mesh(parent, new T.TubeGeometry(path, segments, radius, 8, false), material);
}

function stage(cameraPosition, target, cool = 12, warm = 13) {
  const scene = new T.Scene();
  const camera = new T.PerspectiveCamera(34, 1, .1, 70);
  camera.position.set(...cameraPosition);
  camera.lookAt(...target);
  scene.add(new T.HemisphereLight(0xc1e5ff, 0x624637, 1.35));
  const rim = new T.PointLight(cyan, cool, 0, 2);
  const arc = new T.PointLight(0xff7b32, warm, 0, 2);
  rim.position.set(-3, 2, 4);
  arc.position.set(3, -1, 3);
  scene.add(rim, arc);
  return { scene, camera };
}

function sparks(scene) {
  const count = 38;
  const data = new Float32Array(count * 3);
  const speed = Array.from({ length: count }, () =>
    vector((Math.random() - .4) * 4, Math.random() * 3.4, (Math.random() - .3) * 3));
  const geo = new T.BufferGeometry();
  geo.setAttribute('position', new T.BufferAttribute(data, 3));
  const mat = new T.PointsMaterial({
    color: 0xffa044, size: .055, transparent: true, blending: T.AdditiveBlending,
    depthWrite: false, toneMapped: false
  });
  const points = new T.Points(geo, mat);
  points.visible = false;
  points.frustumCulled = false;
  scene.add(points);
  let age = 1;
  return {
    start(position) {
      points.position.copy(position);
      age = 0;
    },
    step(dt, still) {
      age += dt;
      points.visible = !still && age < .6;
      if (!points.visible) return;
      for (let i = 0; i < count; i++) {
        data[3 * i] = speed[i].x * age;
        data[3 * i + 1] = speed[i].y * age - 3 * age ** 2;
        data[3 * i + 2] = speed[i].z * age;
      }
      geo.attributes.position.needsUpdate = true;
      mat.opacity = 1 - age / .6;
    }
  };
}

function pick(e, canvas, camera, objects) {
  const bounds = canvas.getBoundingClientRect();
  const ray = new T.Raycaster();
  ray.setFromCamera(new T.Vector2(
    (e.clientX - bounds.left) / bounds.width * 2 - 1,
    -((e.clientY - bounds.top) / bounds.height * 2 - 1)
  ), camera);
  return ray.intersectObjects(objects, false)[0];
}

function gear(parent, teeth, pitch, depth, material) {
  const face = new T.Shape();
  const radius = pitch + .13;
  const root = pitch - .12;
  const steps = [[-.50, root], [-.27, root], [-.17, radius], [.17, radius], [.27, root]];
  for (let i = 0; i < teeth; i++) {
    steps.forEach(([offset, r], step) => {
      const a = (i + offset) * turn / teeth;
      const x = Math.cos(a) * r;
      const y = Math.sin(a) * r;
      if (i === 0 && step === 0) face.moveTo(x, y);
      else face.lineTo(x, y);
    });
  }
  face.closePath();
  const bore = new T.Path();
  bore.absarc(0, 0, pitch * .26, 0, turn, true);
  face.holes.push(bore);
  for (let i = 0; i < 6; i++) {
    const hole = new T.Path();
    const a = i * turn / 6;
    hole.absarc(Math.cos(a) * pitch * .61, Math.sin(a) * pitch * .61, pitch * .13, 0, turn, true);
    face.holes.push(hole);
  }
  const geometry = new T.ExtrudeGeometry(face, {
    depth, bevelEnabled: true, bevelSize: .024, bevelThickness: .028, bevelSegments: 2, curveSegments: 15
  });
  return mesh(parent, geometry, material);
}

function brushedMetal() {
  const data = new Uint8Array(128 * 32 * 4);
  for (let y = 0; y < 32; y++) {
    for (let x = 0; x < 128; x++) {
      const i = (y * 128 + x) * 4;
      const value = 130 + Math.sin(x * 2.3) * 30 + Math.sin(x * .23 + y * .16) * 18;
      data.set([value, value, value, 255], i);
    }
  }
  const texture = new T.DataTexture(data, 128, 32);
  texture.wrapS = texture.wrapT = T.RepeatWrapping;
  texture.repeat.set(.85, .85);
  texture.magFilter = T.LinearFilter;
  texture.needsUpdate = true;
  return texture;
}

function circuit(parent) {
  const board = new T.Group();
  parent.add(board);
  board.position.set(-1.68, -.89, -.42);
  board.rotation.z = .13;
  const pcb = metal(0x164c46, .35, .59);
  const pins = metal(0xbda878);
  const chip = metal(0x13191f, .15, .65);
  box(board, [2.08, 1.4, .13], pcb, [0, 0, 0]);
  box(board, [.62, .53, .12], chip, [.12, .03, .125]);
  box(board, [.45, .27, .13], chip, [-.54, -.33, .12]);
  for (let i = 0; i < 11; i++) {
    const x = -.86 + i * .162;
    box(board, [.065, .16, .06], pins, [x, .59, .095]);
    box(board, [.067, .16, .06], pins, [x, -.59, .095]);
    const end = i < 6 ? .19 : -.17;
    tube(board, curve([[x, end > 0 ? .48 : -.48, .07], [x, end, .07], [x + .18, end * .62, .07]]), .008, pins, 9);
  }
  box(board, [.20, .09, .035], glow(0x66f7f4), [-.68, .37, .10]);
}

function drive(element, canvas, refresh) {
  const { scene, camera } = stage([.35, .35, 9.9], [0, 0, 0]);
  const rig = new T.Group();
  scene.add(rig);
  rig.rotation.set(-.19, -.31, -.12);
  circuit(rig);
  const frame = metal(0x25303b, .68, .4);
  const silver = metal(steel);
  silver.roughnessMap = brushedMetal();
  const smallMaterial = metal(0xb1ada0, .85, .25);
  smallMaterial.roughnessMap = silver.roughnessMap;
  const main = gear(rig, 24, 1.45, .34, silver);
  const small = gear(rig, 14, 1.45 * 14 / 24, .30, smallMaterial);
  const angle = -.30;
  main.position.set(-.67, .32, .22);
  small.position.set(-.67 + 2.30 * Math.cos(angle), .32 + 2.30 * Math.sin(angle), .22);
  small.rotation.z = angle + Math.PI + Math.PI / 14 - angle * 24 / 14;
  const hub = metal(0x73848d, .8, .29);
  for (const [wheel, r] of [[main, 1.45], [small, 1.45 * 14 / 24]]) {
    mesh(wheel, new T.TorusGeometry(r * .35, .031, 10, 50), hub, 0, 0, .355);
    mesh(rig, new T.CylinderGeometry(r * .39, r * .39, .36, 40), frame,
      wheel.position.x, wheel.position.y, .04).rotation.x = Math.PI / 2;
    mesh(rig, new T.CylinderGeometry(r * .18, r * .18, .51, 24), smallMaterial,
      wheel.position.x, wheel.position.y, .30).rotation.x = Math.PI / 2;
    mesh(rig, new T.CylinderGeometry(r * .09, r * .09, .09, 6), frame,
      wheel.position.x, wheel.position.y, .59).rotation.x = Math.PI / 2;
  }
  const routes = [
    [[-3.65, -.98, -.65], [-2.62, -1.54, -.16], [-1.38, -1.88, .72], [.35, -1.62, 1.21], [2.3, -.85, .64], [3.5, .38, -.65]],
    [[-3.70, -1.21, -.54], [-2.43, -1.91, .05], [-.84, -2.04, .92], [.84, -1.63, 1.35], [2.45, -.68, .72], [3.54, .72, -.75]],
    [[-3.65, -.73, -.75], [-2.80, -1.19, -.38], [-1.16, -1.62, .51], [.20, -1.44, 1.0], [2.18, -.50, .43], [3.5, .1, -.81]]
  ].map(curve);
  const cable = [metal(0x294e58, .28, .47), metal(copper), metal(0x183535, .18, .42)];
  const pulse = glow(0xaefaff);
  const dots = routes.map((path, i) => {
    tube(rig, path, .064, cable[i], 56);
    return Array.from({ length: 3 }, () => mesh(rig, new T.SphereGeometry(.041, 9, 7), pulse));
  });

  const burst = sparks(rig);
  const mouse = new T.Vector2();
  let velocity = .22;
  let elapsed = 0;
  let boost = 0;
  const button = element.querySelector('button');
  function activate() {
    boost = 1.65;
    burst.start(vector(main.position.x + 1.46 * Math.cos(angle), main.position.y + 1.46 * Math.sin(angle), .66));
    refresh();
  }
  canvas.addEventListener('pointermove', e => {
    const rect = canvas.getBoundingClientRect();
    mouse.set((e.clientX - rect.left) / rect.width - .5, (e.clientY - rect.top) / rect.height - .5);
    canvas.style.cursor = pick(e, canvas, camera, [main]) ? 'pointer' : '';
  });
  canvas.addEventListener('pointerleave', () => mouse.set(0, 0));
  canvas.addEventListener('click', e => {
    if (pick(e, canvas, camera, [main])) activate();
  });
  button.addEventListener('click', activate);
  return {
    scene, camera, continuous: true,
    update(dt, still) {
      boost = Math.max(0, boost - dt);
      velocity = T.MathUtils.damp(velocity, boost ? 2.1 : .22, 3, dt);
      if (!still) {
        main.rotation.z += velocity * dt;
        small.rotation.z -= velocity * dt * 24 / 14;
        elapsed += dt * (boost ? .32 : .12);
      }
      rig.rotation.x = still ? -.19 : T.MathUtils.damp(rig.rotation.x, -.19 + mouse.y * .23, 5, dt);
      rig.rotation.y = still ? -.31 : T.MathUtils.damp(rig.rotation.y, -.31 + mouse.x * .33, 5, dt);
      routes.forEach((path, i) => dots[i].forEach((dot, j) => {
        const point = (elapsed + j * .31 + i * .075) % 1;
        dot.position.copy(path.getPointAt(point));
        dot.position.z += .069;
        dot.scale.setScalar(.50 + .65 * Math.sin(point * Math.PI));
      }));
      burst.step(dt, still);
    }
  };
}

function plankTexture(noise) {
  const canvas = document.createElement('canvas');
  canvas.width = 384;
  canvas.height = 128;
  const context = canvas.getContext('2d');
  const image = context.createImageData(canvas.width, canvas.height);
  for (let y = 0; y < canvas.height; y++) {
    for (let x = 0; x < canvas.width; x++) {
      const offset = (y * canvas.width + x) * 4;
      const swirl = noise.noise(x / 185, y / 35);
      const grain = Math.sin(y * .31 + swirl * 5) * 9 + Math.sin(y * 1.21 + swirl * 10) * 5;
      const brightness = grain + noise.noise(x / 37, y / 8) * 9;
      image.data.set([102 + brightness, 61 + brightness * .8, 37 + brightness * .6, 255], offset);
    }
  }
  context.putImageData(image, 0, 0);
  const texture = new T.CanvasTexture(canvas);
  texture.colorSpace = T.SRGBColorSpace;
  texture.wrapS = texture.wrapT = T.RepeatWrapping;
  texture.repeat.set(.21, .47);
  texture.anisotropy = 4;
  return texture;
}

function tabletop(element, canvas, refresh) {
  const target = [0, .83, 0];
  const { scene, camera } = stage([5.7, 3.9, 5.8], target, 6, 12);
  const controls = new OrbitControls(camera, canvas);
  controls.target.set(...target);
  controls.enableDamping = true;
  controls.dampingFactor = .13;
  controls.enablePan = false;
  controls.minPolarAngle = .25;
  controls.maxPolarAngle = Math.PI / 2 - .05;
  controls.minDistance = 4.8;
  controls.maxDistance = 12;
  controls.enableZoom = false;
  controls.update();
  controls.addEventListener('change', refresh);

  let seed = 24719;
  const random = () => {
    seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0;
    return seed / 4294967296;
  };
  const noise = new SimplexNoise({ random });
  const grain = plankTexture(noise);
  const walnut = new T.MeshStandardMaterial({ color: 0xa88c7b, map: grain, roughness: .41 });
  const black = metal(0x141a20, .59, .37);
  const flakes = metal(0xffc56d, .82, .25);
  const epoxy = new T.MeshPhysicalMaterial({
    color: 0x12ced4, transmission: .85, ior: 1.5, thickness: 1.2, roughness: .16,
    attenuationDistance: 1.15, attenuationColor: 0x51f7ef, clearcoat: .9
  });
  const gap = (x) => Math.sin(x * 2.45) * .087 + noise.noise(x * 1.7, .72) * .085;
  const west = [];
  const east = [];
  for (let i = 0; i <= 60; i++) {
    const x = -2.25 + i * .075;
    west.push([x, gap(x) - .22 + noise.noise(x * 3.4, 1.75) * .055]);
    east.push([x, gap(x) + .22 + noise.noise(x * 3.6, 2.75) * .07]);
  }
  function slab(points, material, inset = 0) {
    const shape = new T.Shape(points.map(p => new T.Vector2(...p)));
    const model = mesh(scene, new T.ExtrudeGeometry(shape, {
      depth: .18 - inset, bevelEnabled: true, bevelThickness: .012, bevelSize: .011, bevelSegments: 2
    }), material, 0, 1.23, 0);
    model.rotation.x = -Math.PI / 2;
  }
  slab([[-2.25, -1.04], [2.25, -1.04], ...west.slice().reverse()], walnut);
  slab([...east, [2.25, 1.04], [-2.25, 1.04]], walnut);
  slab([...west, ...east.slice().reverse()], epoxy, .006);
  const fleckGeometry = new T.DodecahedronGeometry(.033, 0);
  const flecks = new T.InstancedMesh(fleckGeometry, flakes, 105);
  const fleck = new T.Object3D();
  for (let i = 0; i < flecks.count; i++) {
    const x = (random() - .5) * 4.35;
    fleck.position.set(x, 1.25 + random() * .13, -gap(x) + (random() - .5) * .29);
    fleck.rotation.set(random() * turn, random() * turn, random() * turn);
    fleck.scale.set(.4 + random() * .55, .13, .4 + random() * .58);
    fleck.updateMatrix();
    flecks.setMatrixAt(i, fleck.matrix);
  }
  scene.add(flecks);
  for (const x of [-1.82, 1.82]) {
    for (const z of [-.73, .73]) {
      const side = Math.sign(z);
      box(scene, [.31, .055, .22], black, [x, 1.20, z]);
      tube(scene, curve([
        [x - .13, 1.18, z], [x - .07, .61, z + side * .10],
        [x, .06, z + side * .24], [x + .07, .61, z + side * .11], [x + .13, 1.18, z]
      ]), .041, black, 26);
    }
  }
  const shadowMap = document.createElement('canvas');
  shadowMap.width = shadowMap.height = 128;
  const shade = shadowMap.getContext('2d');
  const gradient = shade.createRadialGradient(64, 64, 8, 64, 64, 63);
  gradient.addColorStop(0, '#000a');
  gradient.addColorStop(1, '#0000');
  shade.fillStyle = gradient;
  shade.fillRect(0, 0, 128, 128);
  const shadow = mesh(scene, new T.PlaneGeometry(6.7, 3.3), new T.MeshBasicMaterial({
    map: new T.CanvasTexture(shadowMap), transparent: true, depthWrite: false
  }), 0, -.026, 0);
  shadow.rotation.x = -Math.PI / 2;
  const led = new T.PointLight(cyan, 0, 3, 2);
  led.position.set(0, .95, 0);
  scene.add(led);
  const ledStrip = box(scene, [3.9, .035, .075], glow(cyan), [0, 1.205, 0]);
  ledStrip.visible = false;
  element.querySelectorAll('[data-resin]').forEach(button => {
    button.addEventListener('click', () => {
      element.querySelector('[data-resin][aria-pressed="true"]').setAttribute('aria-pressed', 'false');
      button.setAttribute('aria-pressed', 'true');
      epoxy.color.set(button.dataset.resin);
      epoxy.attenuationColor.copy(epoxy.color).lerp(new T.Color(0xffffff), .3);
      led.color.copy(epoxy.color);
      ledStrip.material.color.copy(epoxy.color);
      refresh();
    });
  });
  const toggle = element.querySelector('[data-led]');
  toggle.addEventListener('click', () => {
    const on = toggle.getAttribute('aria-pressed') !== 'true';
    toggle.setAttribute('aria-pressed', String(on));
    ledStrip.visible = on;
    led.intensity = on ? 13 : 0;
    refresh();
  });
  element.querySelectorAll('[data-orbit]').forEach(button => {
    button.addEventListener('click', () => {
      if (button.dataset.orbit === 'reset') controls.reset();
      else {
        const offset = camera.position.clone().sub(controls.target);
        const movement = button.dataset.orbit;
        if (movement === 'closer' || movement === 'farther') {
          const distance = offset.length() * (movement === 'closer' ? .82 : 1.22);
          offset.setLength(T.MathUtils.clamp(distance, controls.minDistance, controls.maxDistance));
        } else {
          offset.applyAxisAngle(camera.up, Number(movement));
        }
        camera.position.copy(controls.target).add(offset);
        controls.update();
      }
      refresh();
    });
  });
  return { scene, camera, update(dt, still) {
    controls.enableDamping = !still;
    return controls.update();
  } };
}


function cabinet(element, canvas, refresh) {
  const { scene, camera } = stage([.25, .36, 6.85], [0, 0, 0]);
  const shell = metal(0x35444a, .32, .68);
  const backing = metal(0x192731, .47, .51);
  const rail = metal(0x91a3a9, .82, .37);
  const black = metal(0x161d22, .3, .55);
  box(scene, [4.45, 2.65, .22], backing, [0, 0, -.36]);
  for (const x of [-2.19, 2.19]) box(scene, [.11, 2.65, .66], shell, [x, 0, -.11]);
  for (const y of [-1.29, 1.29]) box(scene, [4.5, .11, .66], shell, [0, y, -.11]);
  const lid = new T.Group();
  lid.position.set(-2.23, 0, -.26);
  lid.rotation.y = -.74;
  scene.add(lid);
  box(lid, [1.15, 2.55, .09], shell, [-.56, 0, .01]);
  box(lid, [.08, .49, .08], rail, [-1.03, 0, .07]);
  box(scene, [4.03, .28, .14], rail, [0, .09, -.17]);
  for (const x of [-1.72, -1.18]) {
    box(scene, [.39, .58, .33], black, [x, .14, .06]);
    box(scene, [.23, .12, .05], rail, [x, .23, .24]);
    box(scene, [.22, .08, .06], glow(0x398996), [x, .08, .24]);
  }
  box(scene, [3.65, .25, .26], shell, [.08, -.94, .09]);
  box(scene, [3.65, .25, .26], shell, [.08, .83, .09]);
  const statusLight = mesh(scene, new T.SphereGeometry(.093, 10, 8), glow(0x00b4cb), 1.78, 1.05, .32);
  const displayCanvas = document.createElement('canvas');
  displayCanvas.width = 256;
  displayCanvas.height = 64;
  const displayContext = displayCanvas.getContext('2d');
  const displayTexture = new T.CanvasTexture(displayCanvas);
  displayTexture.colorSpace = T.SRGBColorSpace;
  mesh(scene, new T.PlaneGeometry(.85, .22), new T.MeshBasicMaterial({
    map: displayTexture, toneMapped: false
  }), .98, 1.065, .255);
  function display(text, color) {
    displayContext.fillStyle = '#0d1a1d';
    displayContext.fillRect(0, 0, 256, 64);
    displayContext.fillStyle = color;
    displayContext.font = 'bold 36px monospace';
    displayContext.textAlign = 'center';
    displayContext.fillText(text, 128, 45);
    displayTexture.needsUpdate = true;
  }

  const colors = { red: 0xd64a45, blue: 0x2489fa, yellow: 0xe9b526, green: 0x20ad6c };
  const wires = Object.entries(colors).map(([name, color], i) => {
    const x = -.81 + i * .70;
    const path = curve([[x, .75, .24], [x + .24, .43, .48], [x + .20, .03, .60],
      [x - .17, -.39, .51], [x, -.83, .25]]);
    const material = metal(color, .17, .38);
    const wire = tube(scene, path, .078, material, 32);
    wire.userData.name = name;
    const split = path.getPoint(.5);
    const pieces = [[0, .485], [.515, 1]].map(([start, end], side) => {
      const pivot = path.getPoint(side === 0 ? 0 : 1);
      const points = Array.from({ length: 15 }, (_, n) =>
        path.getPoint(start + (end - start) * n / 14).sub(pivot));
      const piece = new T.Group();
      piece.position.copy(pivot);
      tube(piece, new T.CatmullRomCurve3(points), .078, material, 20);
      const endPoint = points[side === 0 ? points.length - 1 : 0];
      mesh(piece, new T.SphereGeometry(.054, 8, 6), metal(copper), ...endPoint);
      piece.visible = false;
      scene.add(piece);
      return piece;
    });
    for (const y of [.83, -.94]) {
      mesh(scene, new T.CylinderGeometry(.097, .097, .075, 12), rail, x, y, .24).rotation.x = Math.PI / 2;
      box(scene, [.12, .022, .025], black, [x, y, .285]).rotation.z = .42;
    }
    return { wire, pieces, split, material };
  });

  const buttons = [...element.parentElement.querySelectorAll('[data-wire]')];
  const burst = sparks(scene);
  const hitMeshes = wires.map(item => item.wire);
  let cut;
  let age = 0;
  let success = false;
  function highlight(selected) {
    wires.forEach(item => {
      item.material.emissive.setHex(item.wire === selected && !cut ? colors[selected.userData.name] : 0);
      item.material.emissiveIntensity = .55;
    });
    canvas.classList.toggle('wire-hover', !!selected && !cut);
    refresh();
  }
  canvas.addEventListener('pointermove', e => highlight(pick(e, canvas, camera, hitMeshes)?.object));
  canvas.addEventListener('pointerleave', () => highlight(null));
  canvas.addEventListener('click', e => {
    if (cut) return;
    const hit = pick(e, canvas, camera, hitMeshes);
    if (hit) buttons.find(button => button.dataset.wire === hit.object.userData.name)?.click();
  });
  function showRound(wire, won) {
    cut = wires.find(item => item.wire.userData.name === wire);
    age = 0;
    success = won;
    wires.forEach(item => {
      item.wire.visible = item !== cut;
      item.pieces.forEach(piece => {
        piece.visible = item === cut;
        piece.rotation.set(0, 0, 0);
      });
    });
    highlight(null);
    if (cut && !success) burst.start(cut.split);
    statusLight.material.color.setHex(cut ? (success ? 0x40e995 : 0xff791e) : cyan);
    display(cut ? (success ? '0.0 V' : 'ZWARCIE') : 'SYM 24 V',
      cut ? (success ? '#72fbb2' : '#ff9b62') : '#6de9f4');
    refresh();
  }
  element.addEventListener('warsztat:wire', ({ detail }) => showRound(detail.wire, detail.success));
  showRound(element.dataset.cut, element.dataset.success === 'true');
  return { scene, camera, update(dt, still) {
    age += dt;
    if (cut) {
      const drop = still ? 1 : Math.min(1, age ** 2 * 4.25);
      cut.pieces[0].rotation.x = -drop * .66;
      cut.pieces[0].rotation.z = drop * .38;
      cut.pieces[1].rotation.x = drop * .85;
      cut.pieces[1].rotation.z = -drop * .20;
    }
    const shake = cut && !success && !still ? Math.max(0, .32 - age) : 0;
    statusLight.visible = shake === 0 || Math.sin(age * 40) > -.3;
    camera.position.x = .25 + Math.sin(age * 67) * shake * .34;
    camera.lookAt(0, 0, 0);
    burst.step(dt, still);
    return !!cut && age < .66;
  } };
}

function service(type, element, refresh) {
  const { scene, camera } = stage([3.2, 2.35, 5.3], [0, .07, 0], 14, 16);
  const rig = new T.Group();
  scene.add(rig);
  const silver = metal(0x9ca7ad);
  const brass = metal(copper);
  const dark = metal(0x28323c, .64, .42);
  const light = glow(0x70efff);
  const rotor = new T.Group();
  rig.add(rotor);
  let arc;
  let arcCore;
  if (type === 'rotor') {
    cylinder(rotor, .18, 2.12, silver, [0, 0, 0]);
    for (const y of [-.63, .63]) {
      cylinder(rotor, .71, .16, silver, [0, y, 0], 12);
      cylinder(rotor, .27, .12, dark, [0, y * 1.22, 0], 18);
    }
    for (let i = 0; i < 10; i++) {
      const coil = mesh(rotor, new T.TorusGeometry(.38, .037, 7, 26), brass);
      coil.position.set(Math.cos(i * turn / 10) * .36, 0, Math.sin(i * turn / 10) * .36);
      coil.rotation.y = -i * turn / 10;
      coil.scale.set(.71, 1.54, 1);
    }
    rotor.rotation.z = -.57;
  } else if (type === 'tig') {
    box(rig, [2.4, .16, 1.35], silver, [0, -.72, 0]);
    box(rig, [1.75, .05, .96], dark, [-.1, -.615, 0]);
    const torch = new T.Group();
    torch.position.set(.04, .12, 0);
    torch.rotation.z = -.58;
    rotor.add(torch);
    cylinder(torch, .22, .96, dark, [0, .51, 0], 24);
    cylinder(torch, .245, .31, metal(0xb77282, .37, .35), [0, -.12, 0], 26);
    cylinder(torch, .05, .37, silver, [0, -.31, 0], 12);
    const path = curve([[0, -.28, 0], [.045, -.35, 0], [-.067, -.42, .01], [.041, -.5, 0], [0, -.59, 0]]);
    arc = tube(rig, path, .026, light, 17);
    arcCore = mesh(rig, new T.SphereGeometry(.12, 14, 9), glow(0xff923e), 0, -.584, 0);
    arcCore.scale.y = .32;
  } else if (type === 'cnc') {
    box(rig, [2.3, .42, 1.35], silver, [0, -.70, 0]);
    box(rig, [1.65, .03, .51], dark, [.1, -.479, .1]);
    cylinder(rotor, .27, 1.1, silver, [0, .39, 0], 24);
    cylinder(rotor, .34, .37, dark, [0, 1.04, 0], 24);
    for (let flute = 0; flute < 4; flute++) {
      const path = curve(Array.from({ length: 18 }, (_, i) => {
        const a = i * .16 + flute * turn / 4;
        return [Math.cos(a) * .25, -.32 + i * .055, Math.sin(a) * .25];
      }));
      tube(rotor, path, .051, brass, 24);
    }
  } else {
    const acrylic = new T.MeshPhysicalMaterial({
      color: 0x88d6ef, transmission: .72, thickness: .7, roughness: .12, ior: 1.48
    });
    box(rotor, [1.45, 1.45, 1.45], acrylic, [0, .08, 0]);
    const lines = new T.LineSegments(new T.EdgesGeometry(new T.BoxGeometry(1.47, 1.47, 1.47)),
      new T.LineBasicMaterial({ color: 0x84d8e8, transparent: true, opacity: .7 }));
    lines.position.y = .08;
    rotor.add(lines);
    arcCore = mesh(rotor, new T.IcosahedronGeometry(.37, 1), light, 0, .08, 0);
    rotor.rotation.z = .24;
  }
  const link = element.closest('a');
  let active = false;
  const setActive = value => { active = value; refresh(); };
  link.addEventListener('pointerenter', () => setActive(true));
  link.addEventListener('pointerleave', () => setActive(false));
  link.addEventListener('focus', () => setActive(true));
  link.addEventListener('blur', () => setActive(false));
  let time = .3;
  const view = camera.position.clone();
  return { scene, camera, continuous: true, update(dt, still) {
    if (!still) {
      time += dt * (active ? 2 : 1);
      rotor.rotation.y += dt * (active ? (type === 'cnc' ? 7 : 1.85) : .35);
    }
    if (type === 'tig') rotor.rotation.y = 0;
    rig.position.y = still ? 0 : Math.sin(time * 1.41) * .087;
    if (arc) arc.scale.x = still ? 1 : .78 + .26 * Math.sin(time * 16);
    if (arcCore) arcCore.scale.setScalar(still ? 1 : .88 + Math.sin(time * 5) * .12);
    if (arc) arcCore.scale.y *= .32;
    const distance = still ? 1 : T.MathUtils.damp(camera.position.length() / view.length(), active ? .81 : 1, 6, dt);
    camera.position.copy(view).multiplyScalar(distance);
    camera.lookAt(0, .07, 0);
  } };
}

export function mountStages(elements) {
  const renderer = new T.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'low-power' });
  renderer.setClearColor(0, 0);
  renderer.toneMapping = T.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.27;
  renderer.transmissionResolutionScale = .62;
  const generator = new T.PMREMGenerator(renderer);
  const room = new RoomEnvironment();
  const environment = generator.fromScene(room, .06);
  room.dispose();
  generator.dispose();
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  const records = new Map();
  let frame = 0;
  let last = 0;

  function schedule() {
    if (!frame && !document.hidden) frame = requestAnimationFrame(render);
  }

  function render(now) {
    frame = 0;
    const dt = last ? Math.min(.04, (now - last) / 1000) : 1 / 60;
    last = now;
    const still = reduced.matches || document.documentElement.classList.contains('niebo-stop');
    for (const item of records.values()) {
      if (!item.visible) continue;
      if (!item.dirty && (still || (!item.continuous && !item.moving))) continue;
      const { canvas, ctx, camera, scene, element } = item;
      const ratio = Math.min(devicePixelRatio, element.dataset.scene === 'hero' ? 1.5 : 1.25);
      const width = Math.round(canvas.clientWidth * ratio);
      const height = Math.round(canvas.clientHeight * ratio);
      if (!width || !height) continue;
      item.dirty = false;
      item.moving = item.update(dt, still);
      if (canvas.width !== width || canvas.height !== height) {
        canvas.width = width;
        canvas.height = height;
      }
      if (renderer.domElement.width !== width || renderer.domElement.height !== height) {
        renderer.setSize(width, height, false);
      }
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
      renderer.render(scene, camera);
      ctx.clearRect(0, 0, width, height);
      ctx.drawImage(renderer.domElement, 0, 0);
      element.classList.add('scene-ready');
      if (!still && (item.continuous || item.moving || item.dirty)) schedule();
    }
  }

  const resize = new ResizeObserver(entries => entries.forEach(({ target }) => records.get(target)?.refresh()));
  const visibility = new IntersectionObserver(entries => {
    entries.forEach(({ isIntersecting, target }) => {
      let item = records.get(target);
      if (isIntersecting && !item) {
        try {
          const canvas = target.querySelector('canvas');
          const type = target.dataset.scene;
          const refresh = () => {
            if (item) item.dirty = true;
            schedule();
          };
          const built = type === 'hero' ? drive(target, canvas, refresh)
            : type === 'table' ? tabletop(target, canvas, refresh)
            : type === 'cabinet' ? cabinet(target, canvas, refresh)
            : service(type, target, refresh);
          built.scene.environment = environment.texture;
          built.scene.environmentIntensity = 1.10;
          item = { ...built, element: target, canvas, ctx: canvas.getContext('2d'), refresh };
          records.set(target, item);
          resize.observe(target);
        } catch (error) {
          target.classList.add('scene-unavailable');
          visibility.unobserve(target);
          console.warn('Podgląd 3D:', error);
        }
      }
      if (item) {
        item.visible = isIntersecting;
        if (isIntersecting) item.refresh();
      }
    });
  });
  elements.forEach(element => visibility.observe(element));
  const refreshAll = () => records.forEach(item => item.refresh());
  reduced.addEventListener('change', refreshAll);
  new MutationObserver(refreshAll).observe(document.documentElement, { attributeFilter: ['class'] });
  document.addEventListener('visibilitychange', refreshAll);
  renderer.domElement.addEventListener('webglcontextlost', () => {
    cancelAnimationFrame(frame);
    visibility.disconnect();
    resize.disconnect();
    records.clear();
    elements.forEach(element => {
      element.classList.remove('scene-ready');
      element.classList.add('scene-unavailable');
    });
  });
}
