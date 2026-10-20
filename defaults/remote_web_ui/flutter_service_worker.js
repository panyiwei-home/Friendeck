'use strict';
const MANIFEST = 'flutter-app-manifest';
const TEMP = 'flutter-temp-cache';
const CACHE_NAME = 'flutter-app-cache';

const RESOURCES = {"assets/AssetManifest.bin": "499dfc7b959ad4b3e78d8ad64b72c98c",
"assets/AssetManifest.bin.json": "f9730f849f160e682324671ce50fb1db",
"assets/assets/app-logo.ico": "7dde9be0df3ac7bc1d331450284852a7",
"assets/assets/app-logo.png": "5ba77ebffe24e9303fd564ad2b46ff15",
"assets/assets/steamdeck-home.png": "a405c42a216649bee91206eee81bce54",
"assets/assets/tubiaobao/mimetypes/application-certificate.svg": "5f9606bac94de0348d560d1c496ac29e",
"assets/assets/tubiaobao/mimetypes/application-x-addon.svg": "a5f74405a3737fd404bf9113d8561b31",
"assets/assets/tubiaobao/mimetypes/application-x-executable.svg": "3b658de457f0f1eaffccfc3108c9664e",
"assets/assets/tubiaobao/mimetypes/application-x-firmware.svg": "dec010ef27007cb348a1cfc2e28a0fec",
"assets/assets/tubiaobao/mimetypes/application-x-generic.svg": "3988d00d2b2ca3292036c1f658ceb769",
"assets/assets/tubiaobao/mimetypes/application-x-sharedlib.svg": "5db9388e5391fc68338f2edd5d4f684d",
"assets/assets/tubiaobao/mimetypes/audio-x-generic.svg": "cb448bca271e1dcb493382a12b8272d2",
"assets/assets/tubiaobao/mimetypes/font-x-generic.svg": "5cea816e15a360a6f2795ac6bb2974b0",
"assets/assets/tubiaobao/mimetypes/image-x-generic.svg": "d4fce0583073fe7bc14a1f60b3be84d0",
"assets/assets/tubiaobao/mimetypes/inode-directory.svg": "b6d42954c65e4da94572ebc815e6b2a7",
"assets/assets/tubiaobao/mimetypes/inode-symlink.svg": "7ff39eeb5b0213376314dbce1c2ff5a1",
"assets/assets/tubiaobao/mimetypes/model.svg": "4443511727c06069ffd0dca2107ec080",
"assets/assets/tubiaobao/mimetypes/package-x-generic.svg": "011b8e7cea6431498bcb54303cc3b8ae",
"assets/assets/tubiaobao/mimetypes/text-html.svg": "8107b517309b9b4eba7d1c92bb9e6cd4",
"assets/assets/tubiaobao/mimetypes/text-x-generic.svg": "61e9f6a0d9f3b085ea8b0de898f90d91",
"assets/assets/tubiaobao/mimetypes/text-x-preview.svg": "3988d00d2b2ca3292036c1f658ceb769",
"assets/assets/tubiaobao/mimetypes/text-x-script.svg": "3ac5ff701cbfe577a95dd45c6aa32418",
"assets/assets/tubiaobao/mimetypes/video-x-generic.svg": "3e156acb22c73c3844252659aa5ee6a1",
"assets/assets/tubiaobao/mimetypes/x-office-addressbook.svg": "a38b3c78a70a0deda94b7c34b5783911",
"assets/assets/tubiaobao/mimetypes/x-office-document-template.svg": "06b9c469f18f02e3667522109664faff",
"assets/assets/tubiaobao/mimetypes/x-office-document.svg": "c8fcf992d0aed7cacd263ae82f8cd32b",
"assets/assets/tubiaobao/mimetypes/x-office-drawing.svg": "f9bbcec5b799557ac40c94d4c3077067",
"assets/assets/tubiaobao/mimetypes/x-office-presentation-template.svg": "0150dcd13b2a1882277ac1ef0a31611d",
"assets/assets/tubiaobao/mimetypes/x-office-presentation.svg": "85a5dcb5444aaa60f3fceb214cd0f255",
"assets/assets/tubiaobao/mimetypes/x-office-spreadsheet-template.svg": "c34b3b6d178eb47da4d29aaf3f0fe744",
"assets/assets/tubiaobao/mimetypes/x-office-spreadsheet.svg": "109be1634d8fd2f6fe61899f216220f2",
"assets/assets/tubiaobao/mimetypes/x-package-repository.svg": "f48c34124e1ae6a54f651597f7005ecc",
"assets/assets/tubiaobao/places/folder-documents.svg": "f4a117baf554a8aa22708cd941048aef",
"assets/assets/tubiaobao/places/folder-download.svg": "4c217c5312829f571c73dd2cbfaa06cf",
"assets/assets/tubiaobao/places/folder-drag-accept.svg": "b6d42954c65e4da94572ebc815e6b2a7",
"assets/assets/tubiaobao/places/folder-music.svg": "eac201841359bac918cbfe2608a61fe5",
"assets/assets/tubiaobao/places/folder-pictures.svg": "cc5c7508fbaa7c74c1247b1aa4c78538",
"assets/assets/tubiaobao/places/folder-publicshare.svg": "bb761475ab5664c9167a314848cb7319",
"assets/assets/tubiaobao/places/folder-remote.svg": "387dac07c323a2a70a21f6a69b32237c",
"assets/assets/tubiaobao/places/folder-templates.svg": "613da642e7b3e5b73bc3f4691c0f8aea",
"assets/assets/tubiaobao/places/folder-videos.svg": "6b5bbfbfd27f536701112b8688757f71",
"assets/assets/tubiaobao/places/folder.svg": "b6d42954c65e4da94572ebc815e6b2a7",
"assets/assets/tubiaobao/places/network-server.svg": "7ce226edf96d0db15085b82c6a5a5ba0",
"assets/assets/tubiaobao/places/network-workgroup.svg": "79aca5489c6e0f89ae96014b4a5e78bd",
"assets/assets/tubiaobao/places/user-bookmarks.svg": "c0be64bc2d9949831f91dc072e025af2",
"assets/assets/tubiaobao/places/user-desktop.svg": "e303ac466674e74cad35199741bcca3d",
"assets/assets/tubiaobao/places/user-home.svg": "30a2e9b655063ca9894194efbdbf7301",
"assets/assets/tubiaobao/places/user-trash.svg": "8e504f47b371a9d5874762113361ceb9",
"assets/FontManifest.json": "dc3d03800ccca4601324923c0b1d6d57",
"assets/fonts/MaterialIcons-Regular.otf": "b6ebb221aca2e2ac45870f6139d32960",
"assets/NOTICES": "12a40acf027370fd9ecc0bd5835e25bb",
"assets/packages/cupertino_icons/assets/CupertinoIcons.ttf": "33b7d9392238c04c131b6ce224e13711",
"assets/shaders/ink_sparkle.frag": "ecc85a2e95f5e9f53123dcaf8cb9b6ce",
"assets/shaders/stretch_effect.frag": "40d68efbbf360632f614c731219e95f0",
"canvaskit/canvaskit.js": "8331fe38e66b3a898c4f37648aaf7ee2",
"canvaskit/canvaskit.js.symbols": "a3c9f77715b642d0437d9c275caba91e",
"canvaskit/canvaskit.wasm": "9b6a7830bf26959b200594729d73538e",
"canvaskit/chromium/canvaskit.js": "a80c765aaa8af8645c9fb1aae53f9abf",
"canvaskit/chromium/canvaskit.js.symbols": "e2d09f0e434bc118bf67dae526737d07",
"canvaskit/chromium/canvaskit.wasm": "a726e3f75a84fcdf495a15817c63a35d",
"canvaskit/skwasm.js": "8060d46e9a4901ca9991edd3a26be4f0",
"canvaskit/skwasm.js.symbols": "3a4aadf4e8141f284bd524976b1d6bdc",
"canvaskit/skwasm.wasm": "7e5f3afdd3b0747a1fd4517cea239898",
"canvaskit/skwasm_heavy.js": "740d43a6b8240ef9e23eed8c48840da4",
"canvaskit/skwasm_heavy.js.symbols": "0755b4fb399918388d71b59ad390b055",
"canvaskit/skwasm_heavy.wasm": "b0be7910760d205ea4e011458df6ee01",
"favicon.png": "ad5952df3a9b55c80d5edd1d43205557",
"flutter.js": "24bc71911b75b5f8135c949e27a2984e",
"flutter_bootstrap.js": "97390993c0c90f225895fef9ada2c288",
"icons/Icon-192.png": "a707c94bf0ebf4751f02e9f507a5dceb",
"icons/Icon-512.png": "e56c1f9920231332414729c0878936fe",
"icons/Icon-maskable-192.png": "a707c94bf0ebf4751f02e9f507a5dceb",
"icons/Icon-maskable-512.png": "e56c1f9920231332414729c0878936fe",
"index.html": "3755a15d22b8c7596523be2f6aff28d8",
"/": "3755a15d22b8c7596523be2f6aff28d8",
"main.dart.js": "f3fa86cb065431546318c8535e603045",
"manifest.json": "a8799a5d9c5b468c23133dc83f4ccd91",
"version.json": "af7784b1dd9cc426efa392b5e75f393c"};
// The application shell files that are downloaded before a service worker can
// start.
const CORE = ["main.dart.js",
"index.html",
"flutter_bootstrap.js",
"assets/AssetManifest.bin.json",
"assets/FontManifest.json"];

// During install, the TEMP cache is populated with the application shell files.
self.addEventListener("install", (event) => {
  self.skipWaiting();
  return event.waitUntil(
    caches.open(TEMP).then((cache) => {
      return cache.addAll(
        CORE.map((value) => new Request(value, {'cache': 'reload'})));
    })
  );
});
// During activate, the cache is populated with the temp files downloaded in
// install. If this service worker is upgrading from one with a saved
// MANIFEST, then use this to retain unchanged resource files.
self.addEventListener("activate", function(event) {
  return event.waitUntil(async function() {
    try {
      var contentCache = await caches.open(CACHE_NAME);
      var tempCache = await caches.open(TEMP);
      var manifestCache = await caches.open(MANIFEST);
      var manifest = await manifestCache.match('manifest');
      // When there is no prior manifest, clear the entire cache.
      if (!manifest) {
        await caches.delete(CACHE_NAME);
        contentCache = await caches.open(CACHE_NAME);
        for (var request of await tempCache.keys()) {
          var response = await tempCache.match(request);
          await contentCache.put(request, response);
        }
        await caches.delete(TEMP);
        // Save the manifest to make future upgrades efficient.
        await manifestCache.put('manifest', new Response(JSON.stringify(RESOURCES)));
        // Claim client to enable caching on first launch
        self.clients.claim();
        return;
      }
      var oldManifest = await manifest.json();
      var origin = self.location.origin;
      for (var request of await contentCache.keys()) {
        var key = request.url.substring(origin.length + 1);
        if (key == "") {
          key = "/";
        }
        // If a resource from the old manifest is not in the new cache, or if
        // the MD5 sum has changed, delete it. Otherwise the resource is left
        // in the cache and can be reused by the new service worker.
        if (!RESOURCES[key] || RESOURCES[key] != oldManifest[key]) {
          await contentCache.delete(request);
        }
      }
      // Populate the cache with the app shell TEMP files, potentially overwriting
      // cache files preserved above.
      for (var request of await tempCache.keys()) {
        var response = await tempCache.match(request);
        await contentCache.put(request, response);
      }
      await caches.delete(TEMP);
      // Save the manifest to make future upgrades efficient.
      await manifestCache.put('manifest', new Response(JSON.stringify(RESOURCES)));
      // Claim client to enable caching on first launch
      self.clients.claim();
      return;
    } catch (err) {
      // On an unhandled exception the state of the cache cannot be guaranteed.
      console.error('Failed to upgrade service worker: ' + err);
      await caches.delete(CACHE_NAME);
      await caches.delete(TEMP);
      await caches.delete(MANIFEST);
    }
  }());
});
// The fetch handler redirects requests for RESOURCE files to the service
// worker cache.
self.addEventListener("fetch", (event) => {
  if (event.request.method !== 'GET') {
    return;
  }
  var origin = self.location.origin;
  var key = event.request.url.substring(origin.length + 1);
  // Redirect URLs to the index.html
  if (key.indexOf('?v=') != -1) {
    key = key.split('?v=')[0];
  }
  if (event.request.url == origin || event.request.url.startsWith(origin + '/#') || key == '') {
    key = '/';
  }
  // If the URL is not the RESOURCE list then return to signal that the
  // browser should take over.
  if (!RESOURCES[key]) {
    return;
  }
  // If the URL is the index.html, perform an online-first request.
  if (key == '/') {
    return onlineFirst(event);
  }
  event.respondWith(caches.open(CACHE_NAME)
    .then((cache) =>  {
      return cache.match(event.request).then((response) => {
        // Either respond with the cached resource, or perform a fetch and
        // lazily populate the cache only if the resource was successfully fetched.
        return response || fetch(event.request).then((response) => {
          if (response && Boolean(response.ok)) {
            cache.put(event.request, response.clone());
          }
          return response;
        });
      })
    })
  );
});
self.addEventListener('message', (event) => {
  // SkipWaiting can be used to immediately activate a waiting service worker.
  // This will also require a page refresh triggered by the main worker.
  if (event.data === 'skipWaiting') {
    self.skipWaiting();
    return;
  }
  if (event.data === 'downloadOffline') {
    downloadOffline();
    return;
  }
});
// Download offline will check the RESOURCES for all files not in the cache
// and populate them.
async function downloadOffline() {
  var resources = [];
  var contentCache = await caches.open(CACHE_NAME);
  var currentContent = {};
  for (var request of await contentCache.keys()) {
    var key = request.url.substring(origin.length + 1);
    if (key == "") {
      key = "/";
    }
    currentContent[key] = true;
  }
  for (var resourceKey of Object.keys(RESOURCES)) {
    if (!currentContent[resourceKey]) {
      resources.push(resourceKey);
    }
  }
  return contentCache.addAll(resources);
}
// Attempt to download the resource online before falling back to
// the offline cache.
function onlineFirst(event) {
  return event.respondWith(
    fetch(event.request).then((response) => {
      return caches.open(CACHE_NAME).then((cache) => {
        cache.put(event.request, response.clone());
        return response;
      });
    }).catch((error) => {
      return caches.open(CACHE_NAME).then((cache) => {
        return cache.match(event.request).then((response) => {
          if (response != null) {
            return response;
          }
          throw error;
        });
      });
    })
  );
}
