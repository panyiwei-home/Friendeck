import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:math';

import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_svg/flutter_svg.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:http/http.dart' as http;
import 'package:mobile_scanner/mobile_scanner.dart';
import 'package:network_info_plus/network_info_plus.dart';
import 'package:path_provider/path_provider.dart';
import 'package:shared_preferences/shared_preferences.dart';

const int kDefaultPort = 59271;

void main() {
  runApp(const FriendDeckApp());
}

class FriendDeckApp extends StatelessWidget {
  const FriendDeckApp({super.key});

  @override
  Widget build(BuildContext context) {
    final scheme =
        ColorScheme.fromSeed(
          seedColor: const Color(0xFF8E95A2),
          brightness: Brightness.dark,
        ).copyWith(
          primary: const Color(0xFFC4CAD4),
          onPrimary: const Color(0xFF0D0E11),
          secondary: const Color(0xFF9DA4B1),
          onSecondary: const Color(0xFF0E1013),
          surface: const Color(0xFF141518),
          onSurface: const Color(0xFFE8EAED),
          surfaceContainerLowest: const Color(0xFF000000),
          surfaceContainerLow: const Color(0xFF101114),
          surfaceContainer: const Color(0xFF17191D),
          surfaceContainerHigh: const Color(0xFF202328),
          surfaceContainerHighest: const Color(0xFF2A2E34),
          outline: const Color(0xFF6D7480),
          outlineVariant: const Color(0xFF424751),
        );

    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'FriendDeck',
      supportedLocales: const [Locale('en'), Locale('zh')],
      localizationsDelegates: const [
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      localeResolutionCallback: (locale, supportedLocales) {
        if (locale == null) return supportedLocales.first;
        if (locale.languageCode.toLowerCase().startsWith('zh')) {
          return const Locale('zh');
        }
        return const Locale('en');
      },
      theme: ThemeData(
        brightness: Brightness.dark,
        useMaterial3: true,
        colorScheme: scheme,
        textTheme: GoogleFonts.notoSansTextTheme(
          ThemeData(brightness: Brightness.dark).textTheme,
        ).apply(bodyColor: scheme.onSurface, displayColor: scheme.onSurface),
        scaffoldBackgroundColor: Colors.black,
        canvasColor: Colors.black,
        cardTheme: CardThemeData(
          color: scheme.surfaceContainerHigh,
          elevation: 0,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(22),
          ),
        ),
        inputDecorationTheme: InputDecorationTheme(
          filled: true,
          fillColor: scheme.surfaceContainerLow.withValues(alpha: 0.88),
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(14),
            borderSide: BorderSide(color: scheme.outlineVariant),
          ),
          enabledBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(14),
            borderSide: BorderSide(color: scheme.outlineVariant),
          ),
          focusedBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(14),
            borderSide: BorderSide(
              color: scheme.primary.withValues(alpha: 0.8),
            ),
          ),
        ),
      ),
      home: const BootstrapGate(),
    );
  }
}

class BootstrapGate extends StatefulWidget {
  const BootstrapGate({super.key});

  @override
  State<BootstrapGate> createState() => _BootstrapGateState();
}

class _BootstrapGateState extends State<BootstrapGate> {
  late final Future<AppBootstrap> _future;

  @override
  void initState() {
    super.initState();
    _future = LocalStore.load();
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<AppBootstrap>(
      future: _future,
      builder: (context, snapshot) {
        if (!snapshot.hasData) {
          return const Scaffold(
            body: Center(child: CircularProgressIndicator()),
          );
        }
        return ConnectScreen(bootstrap: snapshot.data!);
      },
    );
  }
}

class ConnectScreen extends StatefulWidget {
  const ConnectScreen({super.key, required this.bootstrap});

  final AppBootstrap bootstrap;

  @override
  State<ConnectScreen> createState() => _ConnectScreenState();
}

class _ConnectScreenState extends State<ConnectScreen> {
  late final TextEditingController _host;
  late final TextEditingController _port;

  bool _connecting = false;
  bool _detecting = false;
  String? _hint;
  late List<DeckyEndpoint> _recent;

  @override
  void initState() {
    super.initState();
    _host = TextEditingController(text: widget.bootstrap.initial?.host ?? '');
    _port = TextEditingController(
      text: '${widget.bootstrap.initial?.port ?? kDefaultPort}',
    );
    _recent = List<DeckyEndpoint>.from(widget.bootstrap.recent);
  }

  @override
  void dispose() {
    _host.dispose();
    _port.dispose();
    super.dispose();
  }

  DeckyEndpoint? _parseForm() {
    final host = _host.text.trim();
    final port = int.tryParse(_port.text.trim());
    if (host.isEmpty || port == null || port <= 0 || port > 65535) {
      return null;
    }
    return DeckyEndpoint(host: host, port: port);
  }

  Future<void> _connect() async {
    final s = context.s;
    final endpoint = _parseForm();
    if (endpoint == null) {
      context.toast(s.invalidHostOrPort);
      return;
    }

    setState(() => _connecting = true);
    try {
      final client = DeckyApiClient(endpoint);
      await client.fetchUploadOptions();
      client.dispose();

      await LocalStore.savePrimary(endpoint);
      await LocalStore.pushRecent(endpoint);
      final bootstrap = await LocalStore.load();

      if (!mounted) return;
      Navigator.of(context).pushReplacement(
        MaterialPageRoute<void>(
          builder: (_) =>
              DashboardScreen(endpoint: endpoint, recent: bootstrap.recent),
        ),
      );
    } on ApiException catch (e) {
      context.toast(e.message);
    } catch (_) {
      context.toast(s.connectionFailed);
    } finally {
      if (mounted) {
        setState(() => _connecting = false);
      }
    }
  }

  Future<void> _scanQr() async {
    final result = await Navigator.of(context).push<DeckyEndpoint>(
      MaterialPageRoute<DeckyEndpoint>(builder: (_) => const QrScanScreen()),
    );
    if (result == null || !mounted) return;
    setState(() {
      _host.text = result.host;
      _port.text = '${result.port}';
    });
  }

  Future<void> _detectLan() async {
    final s = context.s;
    setState(() => _detecting = true);
    try {
      final ip = await NetworkInfo().getWifiIP();
      if (!mounted) return;
      setState(() {
        _hint = ip == null || ip.isEmpty
            ? s.lanIpUnavailable
            : s.lanHintWithIp(ip);
      });
    } finally {
      if (mounted) {
        setState(() => _detecting = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final s = context.s;
    return Scaffold(
      body: DecoratedBox(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [Color(0xFF000000), Color(0xFF060709), Color(0xFF0C0D10)],
          ),
        ),
        child: SafeArea(
          child: Center(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(20),
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 540),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'FriendDeck',
                      style: Theme.of(context).textTheme.headlineMedium
                          ?.copyWith(fontWeight: FontWeight.w800),
                    ),
                    const SizedBox(height: 6),
                    Text(s.connectIntro),
                    const SizedBox(height: 16),
                    Card(
                      child: Padding(
                        padding: const EdgeInsets.all(14),
                        child: Column(
                          children: [
                            TextField(
                              controller: _host,
                              decoration: InputDecoration(
                                labelText: s.hostLabel,
                                hintText: '192.168.0.10',
                                prefixIcon: const Icon(Icons.dns_rounded),
                              ),
                            ),
                            const SizedBox(height: 10),
                            TextField(
                              controller: _port,
                              keyboardType: TextInputType.number,
                              decoration: InputDecoration(
                                labelText: s.portLabel,
                                hintText: '$kDefaultPort',
                                prefixIcon: const Icon(Icons.numbers_rounded),
                              ),
                            ),
                            const SizedBox(height: 12),
                            Wrap(
                              spacing: 10,
                              runSpacing: 10,
                              children: [
                                FilledButton.icon(
                                  onPressed: _connecting ? null : _connect,
                                  icon: _connecting
                                      ? const SizedBox(
                                          width: 16,
                                          height: 16,
                                          child: CircularProgressIndicator(
                                            strokeWidth: 2,
                                          ),
                                        )
                                      : const Icon(Icons.link_rounded),
                                  label: Text(
                                    _connecting ? s.connecting : s.connect,
                                  ),
                                ),
                                OutlinedButton.icon(
                                  onPressed: _connecting ? null : _scanQr,
                                  icon: const Icon(
                                    Icons.qr_code_scanner_rounded,
                                  ),
                                  label: Text(s.scanQr),
                                ),
                                OutlinedButton.icon(
                                  onPressed: _detecting ? null : _detectLan,
                                  icon: _detecting
                                      ? const SizedBox(
                                          width: 16,
                                          height: 16,
                                          child: CircularProgressIndicator(
                                            strokeWidth: 2,
                                          ),
                                        )
                                      : const Icon(Icons.wifi_find_rounded),
                                  label: Text(s.detectLan),
                                ),
                              ],
                            ),
                            if (_hint != null) ...[
                              const SizedBox(height: 8),
                              Text(
                                _hint!,
                                style: Theme.of(context).textTheme.bodySmall,
                              ),
                            ],
                          ],
                        ),
                      ),
                    ),
                    if (_recent.isNotEmpty) ...[
                      const SizedBox(height: 14),
                      Text(
                        s.recentEndpoints,
                        style: Theme.of(context).textTheme.titleSmall,
                      ),
                      const SizedBox(height: 8),
                      Wrap(
                        spacing: 8,
                        runSpacing: 8,
                        children: _recent
                            .map(
                              (e) => ActionChip(
                                label: Text(e.label),
                                onPressed: () {
                                  setState(() {
                                    _host.text = e.host;
                                    _port.text = '${e.port}';
                                  });
                                },
                              ),
                            )
                            .toList(),
                      ),
                    ],
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({
    super.key,
    required this.endpoint,
    required this.recent,
  });

  final DeckyEndpoint endpoint;
  final List<DeckyEndpoint> recent;

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  late final DeckyApiClient _client;
  final GlobalKey<_FilesTabState> _filesTabKey = GlobalKey<_FilesTabState>();
  final GlobalKey<_MediaTabState> _mediaTabKey = GlobalKey<_MediaTabState>();
  late final List<Widget> _tabs;
  int _index = 0;
  DateTime? _lastExitBackAt;

  @override
  void initState() {
    super.initState();
    _client = DeckyApiClient(widget.endpoint);
    _tabs = [
      TransferTab(client: _client),
      FilesTab(key: _filesTabKey, client: _client),
      MediaTab(key: _mediaTabKey, client: _client),
      TextTab(client: _client),
    ];
  }

  @override
  void dispose() {
    _client.dispose();
    super.dispose();
  }

  bool _clearSelectionForBack() {
    final didClear = switch (_index) {
      1 => _filesTabKey.currentState?.clearSelectionForBack() ?? false,
      2 => _mediaTabKey.currentState?.clearSelectionForBack() ?? false,
      _ => false,
    };
    if (didClear) {
      _lastExitBackAt = null;
    }
    return didClear;
  }

  Future<void> _handleBackPressed() async {
    if (_clearSelectionForBack()) {
      return;
    }

    final now = DateTime.now();
    final shouldExit =
        _lastExitBackAt != null &&
        now.difference(_lastExitBackAt!) <= const Duration(seconds: 2);
    if (!shouldExit) {
      _lastExitBackAt = now;
      context.toast(context.s.backAgainToExit);
      return;
    }

    _lastExitBackAt = null;
    if (Platform.isAndroid) {
      await SystemNavigator.pop();
      return;
    }
    if (mounted) {
      await Navigator.of(context).maybePop();
    }
  }

  @override
  Widget build(BuildContext context) {
    final s = context.s;
    final scheme = Theme.of(context).colorScheme;
    final width = MediaQuery.sizeOf(context).width;
    final desktop = width >= 1000;
    final page = DecoratedBox(
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: [Color(0xFF000000), Color(0xFF07080B)],
        ),
      ),
      child: IndexedStack(index: _index, children: _tabs),
    );

    late final Widget shell;
    if (!desktop) {
      shell = Scaffold(
        body: page,
        bottomNavigationBar: NavigationBarTheme(
          data: NavigationBarThemeData(
            backgroundColor: scheme.surfaceContainer,
            indicatorColor: scheme.secondaryContainer,
            surfaceTintColor: Colors.transparent,
            labelTextStyle: WidgetStateProperty.resolveWith(
              (states) => Theme.of(context).textTheme.labelMedium?.copyWith(
                fontWeight: states.contains(WidgetState.selected)
                    ? FontWeight.w700
                    : FontWeight.w500,
              ),
            ),
          ),
          child: NavigationBar(
            selectedIndex: _index,
            onDestinationSelected: (value) => setState(() => _index = value),
            destinations: [
              NavigationDestination(
                icon: Icon(Icons.upload_file_outlined),
                selectedIcon: Icon(Icons.upload_file_rounded),
                label: s.navTransfer,
              ),
              NavigationDestination(
                icon: Icon(Icons.folder_copy_outlined),
                selectedIcon: Icon(Icons.folder_copy_rounded),
                label: s.navFiles,
              ),
              NavigationDestination(
                icon: Icon(Icons.photo_library_outlined),
                selectedIcon: Icon(Icons.photo_library_rounded),
                label: s.navMedia,
              ),
              NavigationDestination(
                icon: Icon(Icons.text_snippet_outlined),
                selectedIcon: Icon(Icons.text_snippet_rounded),
                label: s.navText,
              ),
            ],
          ),
        ),
      );
    } else {
      final railExtended = width >= 1320;
      shell = Scaffold(
        body: Row(
          children: [
            SafeArea(
              child: Padding(
                padding: const EdgeInsets.fromLTRB(10, 10, 8, 10),
                child: Container(
                  width: railExtended ? 224 : 88,
                  decoration: BoxDecoration(
                    color: scheme.surfaceContainer,
                    borderRadius: BorderRadius.circular(24),
                    border: Border.all(
                      color: scheme.outlineVariant.withValues(alpha: 0.42),
                    ),
                  ),
                  child: Column(
                    children: [
                      const SizedBox(height: 10),
                      if (railExtended)
                        Padding(
                          padding: const EdgeInsets.fromLTRB(14, 0, 14, 6),
                          child: Text(
                            widget.endpoint.label,
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: Theme.of(context).textTheme.labelMedium
                                ?.copyWith(color: scheme.onSurfaceVariant),
                          ),
                        ),
                      Expanded(
                        child: NavigationRail(
                          extended: railExtended,
                          selectedIndex: _index,
                          groupAlignment: -0.72,
                          onDestinationSelected: (value) =>
                              setState(() => _index = value),
                          backgroundColor: Colors.transparent,
                          indicatorColor: scheme.secondaryContainer,
                          selectedLabelTextStyle: TextStyle(
                            color: scheme.onSecondaryContainer,
                            fontWeight: FontWeight.w700,
                          ),
                          unselectedLabelTextStyle: TextStyle(
                            color: scheme.onSurfaceVariant,
                            fontWeight: FontWeight.w500,
                          ),
                          destinations: [
                            NavigationRailDestination(
                              icon: Icon(Icons.upload_file_outlined),
                              selectedIcon: Icon(Icons.upload_file_rounded),
                              label: Text(s.navTransfer),
                            ),
                            NavigationRailDestination(
                              icon: Icon(Icons.folder_copy_outlined),
                              selectedIcon: Icon(Icons.folder_copy_rounded),
                              label: Text(s.navFiles),
                            ),
                            NavigationRailDestination(
                              icon: Icon(Icons.photo_library_outlined),
                              selectedIcon: Icon(Icons.photo_library_rounded),
                              label: Text(s.navMedia),
                            ),
                            NavigationRailDestination(
                              icon: Icon(Icons.text_snippet_outlined),
                              selectedIcon: Icon(Icons.text_snippet_rounded),
                              label: Text(s.navText),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
            Expanded(child: page),
          ],
        ),
      );
    }

    return PopScope<void>(
      canPop: false,
      onPopInvokedWithResult: (didPop, result) {
        if (didPop) return;
        unawaited(_handleBackPressed());
      },
      child: shell,
    );
  }
}

class TransferTab extends StatefulWidget {
  const TransferTab({super.key, required this.client});

  final DeckyApiClient client;

  @override
  State<TransferTab> createState() => _TransferTabState();
}

class _TransferTabState extends State<TransferTab>
    with AutomaticKeepAliveClientMixin<TransferTab> {
  List<PlatformFile> _picked = const [];
  bool _uploading = false;
  int _uploadedCount = 0;
  String _uploadingName = '';

  @override
  void dispose() => super.dispose();

  Future<void> _pickFiles() async {
    final result = await FilePicker.platform.pickFiles(allowMultiple: true);
    if (result == null) return;
    setState(() {
      _picked = result.files
          .where((f) => f.path != null && f.path!.isNotEmpty)
          .toList();
    });
  }

  Future<String?> _pickUploadDestination(UploadOptions options) async {
    final base = (options.defaultDir ?? '').trim();
    final initialPath = base.isEmpty ? '/home/deck' : base;
    return showModalBottomSheet<String>(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      backgroundColor: Colors.transparent,
      builder: (_) => _UploadPathPickerSheet(
        client: widget.client,
        initialPath: initialPath,
      ),
    );
  }

  Future<void> _uploadPicked() async {
    final s = context.s;
    if (_picked.isEmpty) {
      context.toast(s.selectFilesFirst);
      return;
    }

    String? chosenPath;
    try {
      final options = await widget.client.fetchUploadOptions();
      if (options.promptUploadPath) {
        chosenPath = await _pickUploadDestination(options);
        if (!mounted) return;
        if (chosenPath == null || chosenPath.trim().isEmpty) {
          context.toast(s.chooseUploadPathFirst);
          return;
        }
      }
    } on ApiException catch (e) {
      if (mounted) context.toast(e.message);
      return;
    } catch (_) {
      if (mounted) context.toast(s.uploadPathLoadFailed);
      return;
    }

    setState(() {
      _uploading = true;
      _uploadedCount = 0;
      _uploadingName = '';
    });

    try {
      for (var i = 0; i < _picked.length; i++) {
        final item = _picked[i];
        final path = item.path;
        if (path == null || path.isEmpty) continue;
        setState(() {
          _uploadingName = item.name;
          _uploadedCount = i;
        });
        await widget.client.uploadFile(filePath: path, destPath: chosenPath);
      }
      if (!mounted) return;
      setState(() {
        _uploading = false;
        _uploadedCount = _picked.length;
      });
      context.toast(s.uploadCompleted);
    } on ApiException catch (e) {
      if (mounted) context.toast(e.message);
      if (mounted) setState(() => _uploading = false);
    } catch (_) {
      if (mounted) context.toast(s.uploadFailed);
      if (mounted) setState(() => _uploading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    super.build(context);

    final keyboardInset = MediaQuery.viewInsetsOf(context).bottom;
    const dockHeight = 258.0;

    return SafeArea(
      bottom: false,
      child: LayoutBuilder(
        builder: (context, constraints) {
          final scheme = Theme.of(context).colorScheme;
          final desktop = constraints.maxWidth >= 1100;
          if (desktop) {
            return Padding(
              padding: const EdgeInsets.fromLTRB(16, 16, 16, 14),
              child: Row(
                children: [
                  Expanded(
                    child: Container(
                      decoration: BoxDecoration(
                        color: scheme.surfaceContainerLow,
                        borderRadius: BorderRadius.circular(24),
                        border: Border.all(
                          color: scheme.outlineVariant.withValues(alpha: 0.42),
                        ),
                      ),
                      child: Padding(
                        padding: const EdgeInsets.fromLTRB(12, 10, 12, 10),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              context.s.selectedFiles,
                              style: Theme.of(context).textTheme.titleMedium
                                  ?.copyWith(fontWeight: FontWeight.w700),
                            ),
                            const SizedBox(height: 8),
                            Expanded(
                              child: AnimatedSwitcher(
                                duration: const Duration(milliseconds: 220),
                                switchInCurve: Curves.easeOutCubic,
                                switchOutCurve: Curves.easeInCubic,
                                child: _buildPickedPanel(
                                  context,
                                  desktop: true,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(width: 16),
                  SizedBox(
                    width: 420,
                    child: _buildTransferDock(context, desktop: true),
                  ),
                ],
              ),
            );
          }

          return Stack(
            children: [
              Positioned.fill(
                child: Padding(
                  padding: EdgeInsets.fromLTRB(
                    12,
                    12,
                    12,
                    dockHeight + keyboardInset + 10,
                  ),
                  child: AnimatedSwitcher(
                    duration: const Duration(milliseconds: 220),
                    switchInCurve: Curves.easeOutCubic,
                    switchOutCurve: Curves.easeInCubic,
                    layoutBuilder: (currentChild, previousChildren) {
                      return Stack(
                        fit: StackFit.expand,
                        alignment: Alignment.bottomCenter,
                        children: [
                          ...previousChildren,
                          if (currentChild != null) currentChild,
                        ],
                      );
                    },
                    child: _buildPickedPanel(context),
                  ),
                ),
              ),
              Positioned(
                left: 0,
                right: 0,
                bottom: keyboardInset,
                child: _buildTransferDock(context),
              ),
            ],
          );
        },
      ),
    );
  }

  Widget _buildPickedPanel(BuildContext context, {bool desktop = false}) {
    final theme = Theme.of(context);
    final scheme = theme.colorScheme;

    if (_picked.isEmpty) {
      return Align(
        key: const ValueKey('transfer-empty'),
        alignment: desktop ? Alignment.center : Alignment.bottomCenter,
        child: Padding(
          padding: EdgeInsets.only(bottom: desktop ? 0 : 8),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(
                Icons.upload_file_rounded,
                size: 34,
                color: scheme.primary.withValues(alpha: 0.5),
              ),
              const SizedBox(height: 8),
              Text(
                context.s.noSelectedFiles,
                style: theme.textTheme.titleSmall?.copyWith(
                  fontWeight: FontWeight.w700,
                ),
              ),
              const SizedBox(height: 2),
              Text(
                context.s.transferStackHint,
                style: theme.textTheme.bodySmall?.copyWith(
                  color: scheme.onSurfaceVariant,
                ),
              ),
            ],
          ),
        ),
      );
    }

    return ListView.builder(
      key: const ValueKey('transfer-picked'),
      reverse: !desktop,
      physics: const BouncingScrollPhysics(),
      padding: const EdgeInsets.only(top: 8, bottom: 6),
      itemCount: _picked.length,
      itemBuilder: (context, index) {
        final item = _picked[_picked.length - 1 - index];
        return Padding(
          padding: const EdgeInsets.only(bottom: 10),
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 180),
            curve: Curves.easeOutCubic,
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(18),
              color: scheme.surfaceContainerLow.withValues(alpha: 0.95),
              boxShadow: const [
                BoxShadow(
                  color: Color(0x1E1A304A),
                  blurRadius: 12,
                  offset: Offset(0, 5),
                ),
              ],
            ),
            child: ListTile(
              contentPadding: const EdgeInsets.fromLTRB(12, 8, 6, 8),
              leading: CircleAvatar(
                backgroundColor: scheme.primaryContainer.withValues(
                  alpha: 0.72,
                ),
                child: SizedBox(
                  width: 33,
                  height: 33,
                  child: buildFileSystemIcon(
                    isDir: false,
                    name: item.name,
                    path: item.path ?? item.name,
                    fallbackColor: scheme.onPrimaryContainer,
                  ),
                ),
              ),
              title: Text(
                item.name,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: theme.textTheme.bodyLarge?.copyWith(
                  fontWeight: FontWeight.w600,
                ),
              ),
              subtitle: Text(
                fmtBytes(item.size),
                style: theme.textTheme.bodySmall?.copyWith(
                  color: scheme.onSurfaceVariant,
                ),
              ),
              trailing: IconButton(
                icon: const Icon(Icons.close_rounded),
                onPressed: _uploading
                    ? null
                    : () {
                        setState(() {
                          final next = [..._picked];
                          final removeIndex = next.indexOf(item);
                          if (removeIndex >= 0) {
                            next.removeAt(removeIndex);
                          }
                          _picked = next;
                        });
                      },
              ),
            ),
          ),
        );
      },
    );
  }

  Widget _buildTransferDock(BuildContext context, {bool desktop = false}) {
    final theme = Theme.of(context);
    final scheme = theme.colorScheme;
    final canUpload = _picked.isNotEmpty && !_uploading;

    return Material(
      elevation: desktop ? 1 : 3,
      shadowColor: Colors.black.withValues(alpha: 0.16),
      surfaceTintColor: Colors.transparent,
      color: scheme.surfaceContainer,
      shape: RoundedRectangleBorder(
        borderRadius: desktop
            ? BorderRadius.circular(24)
            : const BorderRadius.only(
                topLeft: Radius.circular(28),
                topRight: Radius.circular(28),
              ),
        side: BorderSide(
          color: scheme.outlineVariant.withValues(alpha: desktop ? 0.42 : 0.3),
        ),
      ),
      clipBehavior: Clip.antiAlias,
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 12),
            child: Container(
              height: 1,
              decoration: BoxDecoration(
                color: scheme.outlineVariant.withValues(alpha: 0.18),
                borderRadius: BorderRadius.circular(999),
              ),
            ),
          ),
          Padding(
            padding: const EdgeInsets.fromLTRB(14, 12, 14, 12),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Expanded(
                      child: FilledButton.tonalIcon(
                        onPressed: _uploading ? null : _pickFiles,
                        icon: const Icon(Icons.attach_file_rounded),
                        label: Text(context.s.pickFiles),
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: OutlinedButton.icon(
                        onPressed: _uploading
                            ? null
                            : () => setState(() => _picked = const []),
                        icon: const Icon(Icons.clear_all_rounded),
                        label: Text(context.s.clear),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 10),
                SizedBox(
                  width: double.infinity,
                  child: FilledButton.icon(
                    onPressed: canUpload ? _uploadPicked : null,
                    icon: _uploading
                        ? const SizedBox(
                            width: 16,
                            height: 16,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : const Icon(Icons.cloud_upload_rounded),
                    label: Text(
                      _uploading ? context.s.uploading : context.s.startUpload,
                    ),
                  ),
                ),
                if (_uploading) ...[
                  const SizedBox(height: 10),
                  LinearProgressIndicator(
                    borderRadius: BorderRadius.circular(99),
                    value: _picked.isEmpty
                        ? null
                        : (_uploadedCount / _picked.length),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    context.s.uploadProgress(
                      _uploadedCount,
                      _picked.length,
                      _uploadingName,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: scheme.onSurfaceVariant,
                    ),
                  ),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }

  @override
  bool get wantKeepAlive => true;
}

class _UploadPathPickerSheet extends StatefulWidget {
  const _UploadPathPickerSheet({
    required this.client,
    required this.initialPath,
  });

  final DeckyApiClient client;
  final String initialPath;

  @override
  State<_UploadPathPickerSheet> createState() => _UploadPathPickerSheetState();
}

class _UploadPathPickerSheetState extends State<_UploadPathPickerSheet> {
  String _path = '/';
  bool _loading = true;
  String? _error;
  List<RemoteFileEntry> _dirs = const [];

  @override
  void initState() {
    super.initState();
    final base = widget.initialPath.trim();
    _load(base.isEmpty ? '/home/deck' : base);
  }

  List<MapEntry<String, String>> _crumbs(String path) {
    final normalized = path.replaceAll('\\', '/').trim();
    if (normalized.isEmpty || normalized == '/') {
      return const [MapEntry('/', '/')];
    }
    final out = <MapEntry<String, String>>[const MapEntry('/', '/')];
    var current = '';
    for (final segment in normalized.split('/').where((e) => e.isNotEmpty)) {
      current += '/$segment';
      out.add(MapEntry(segment, current));
    }
    return out;
  }

  Future<void> _load(String path) async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final result = await widget.client.listFiles(path: path);
      final dirs = result.files.where((e) => e.isDir).toList()
        ..sort((a, b) => a.name.toLowerCase().compareTo(b.name.toLowerCase()));
      if (!mounted) return;
      setState(() {
        _path = result.currentPath;
        _dirs = dirs;
        _loading = false;
      });
    } on ApiException catch (e) {
      if (!mounted) return;
      setState(() {
        _error = e.message;
        _loading = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _error = context.s.uploadPathLoadFailed;
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final s = context.s;
    final theme = Theme.of(context);
    final scheme = theme.colorScheme;
    final crumbs = _crumbs(_path);

    return Padding(
      padding: const EdgeInsets.fromLTRB(10, 0, 10, 10),
      child: Material(
        color: scheme.surfaceContainerHigh,
        elevation: 8,
        shadowColor: Colors.black.withValues(alpha: 0.26),
        borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
        clipBehavior: Clip.antiAlias,
        child: SizedBox(
          height: min(MediaQuery.sizeOf(context).height * 0.78, 560),
          child: Column(
            children: [
              const SizedBox(height: 8),
              Container(
                width: 42,
                height: 4,
                decoration: BoxDecoration(
                  color: scheme.onSurfaceVariant.withValues(alpha: 0.4),
                  borderRadius: BorderRadius.circular(999),
                ),
              ),
              Padding(
                padding: const EdgeInsets.fromLTRB(12, 10, 8, 6),
                child: Row(
                  children: [
                    Expanded(
                      child: Text(
                        s.chooseUploadPathTitle,
                        style: theme.textTheme.titleMedium?.copyWith(
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ),
                    IconButton(
                      tooltip: s.close,
                      onPressed: () => Navigator.of(context).pop(),
                      icon: const Icon(Icons.close_rounded),
                    ),
                  ],
                ),
              ),
              Padding(
                padding: const EdgeInsets.fromLTRB(12, 0, 12, 8),
                child: Align(
                  alignment: Alignment.centerLeft,
                  child: Text(
                    s.uploadPathCurrent(_path),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: scheme.onSurfaceVariant,
                    ),
                  ),
                ),
              ),
              SizedBox(
                height: 34,
                child: SingleChildScrollView(
                  scrollDirection: Axis.horizontal,
                  padding: const EdgeInsets.symmetric(horizontal: 10),
                  child: Row(
                    children: [
                      for (var i = 0; i < crumbs.length; i++) ...[
                        TextButton(
                          onPressed: _loading
                              ? null
                              : () => _load(crumbs[i].value),
                          style: TextButton.styleFrom(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 8,
                              vertical: 0,
                            ),
                            minimumSize: const Size(0, 30),
                            tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                          ),
                          child: Text(
                            crumbs[i].key,
                            style: theme.textTheme.labelMedium?.copyWith(
                              color: crumbs[i].value == _path
                                  ? scheme.onSurface
                                  : scheme.onSurfaceVariant,
                              fontWeight: crumbs[i].value == _path
                                  ? FontWeight.w700
                                  : FontWeight.w500,
                            ),
                          ),
                        ),
                        if (i < crumbs.length - 1)
                          Text(
                            '/',
                            style: theme.textTheme.labelSmall?.copyWith(
                              color: scheme.onSurfaceVariant,
                            ),
                          ),
                      ],
                    ],
                  ),
                ),
              ),
              Padding(
                padding: const EdgeInsets.fromLTRB(12, 8, 12, 10),
                child: Row(
                  children: [
                    OutlinedButton.icon(
                      onPressed: _loading || _path == '/'
                          ? null
                          : () => _load(parentPath(_path)),
                      icon: const Icon(Icons.arrow_upward_rounded),
                      label: Text(s.upLevel),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: FilledButton.icon(
                        onPressed: _loading
                            ? null
                            : () => Navigator.of(context).pop(_path),
                        icon: const Icon(Icons.check_rounded),
                        label: Text(s.selectCurrentFolder),
                      ),
                    ),
                  ],
                ),
              ),
              Divider(
                height: 1,
                color: scheme.outlineVariant.withValues(alpha: 0.35),
              ),
              Expanded(
                child: _loading
                    ? const Center(
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : _error != null
                    ? Center(
                        child: Padding(
                          padding: const EdgeInsets.all(16),
                          child: Column(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Text(
                                _error!,
                                textAlign: TextAlign.center,
                                style: theme.textTheme.bodyMedium,
                              ),
                              const SizedBox(height: 10),
                              FilledButton.tonal(
                                onPressed: () => _load(_path),
                                child: Text(s.retry),
                              ),
                            ],
                          ),
                        ),
                      )
                    : _dirs.isEmpty
                    ? Center(
                        child: Text(
                          s.noSubfolders,
                          style: theme.textTheme.bodyMedium?.copyWith(
                            color: scheme.onSurfaceVariant,
                          ),
                        ),
                      )
                    : ListView.separated(
                        padding: const EdgeInsets.fromLTRB(8, 8, 8, 12),
                        itemCount: _dirs.length,
                        separatorBuilder: (_, _) => const SizedBox(height: 2),
                        itemBuilder: (context, index) {
                          final dir = _dirs[index];
                          return ListTile(
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(12),
                            ),
                            leading: SizedBox(
                              width: 42,
                              height: 42,
                              child: buildFileSystemIcon(
                                isDir: true,
                                name: dir.name,
                                path: dir.path,
                              ),
                            ),
                            title: Text(
                              dir.name,
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                            ),
                            subtitle: Text(
                              dir.path,
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                              style: theme.textTheme.bodySmall?.copyWith(
                                color: scheme.onSurfaceVariant,
                              ),
                            ),
                            trailing: const Icon(Icons.chevron_right_rounded),
                            onTap: _loading ? null : () => _load(dir.path),
                          );
                        },
                      ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

enum FileSort { name, modified, size }

class FilesTab extends StatefulWidget {
  const FilesTab({super.key, required this.client});

  final DeckyApiClient client;

  @override
  State<FilesTab> createState() => _FilesTabState();
}

class _FilesTabState extends State<FilesTab>
    with AutomaticKeepAliveClientMixin<FilesTab> {
  final TextEditingController _search = TextEditingController();

  String _path = '/';
  String? _error;
  bool _loading = true;
  bool _busy = false;
  String _busyMessage = '';
  double? _busyProgress;
  FileSort _sort = FileSort.name;
  bool _desc = false;
  List<RemoteFileEntry> _items = const [];
  final Set<String> _selected = <String>{};
  List<String> _clipboardPaths = const [];
  bool _clipboardCut = false;

  bool get _selectionMode => _selected.isNotEmpty;

  bool clearSelectionForBack() {
    if (_selected.isEmpty) return false;
    setState(() => _selected.clear());
    return true;
  }

  @override
  void initState() {
    super.initState();
    _init();
  }

  @override
  void dispose() {
    _search.dispose();
    super.dispose();
  }

  Future<void> _init() async {
    await _load('/home/deck');
  }

  Future<void> _load(String path) async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final result = await widget.client.listFiles(path: path);
      if (!mounted) return;
      setState(() {
        _path = result.currentPath;
        _items = result.files;
        _selected.clear();
      });
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.message);
    } catch (_) {
      if (mounted) setState(() => _error = context.s.directoryLoadFailed);
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _runBusy(String message, Future<void> Function() action) async {
    setState(() {
      _busy = true;
      _busyMessage = message;
      _busyProgress = null;
    });
    try {
      await action();
    } finally {
      if (mounted) {
        setState(() {
          _busy = false;
          _busyMessage = '';
          _busyProgress = null;
        });
      }
    }
  }

  Future<void> _runBusyWithProgress(
    String initialMessage,
    Future<void> Function(void Function(String, {double? progress}) update)
    action,
  ) async {
    setState(() {
      _busy = true;
      _busyMessage = initialMessage;
      _busyProgress = null;
    });
    try {
      await action((message, {progress}) {
        if (!mounted) return;
        setState(() {
          _busyMessage = message;
          _busyProgress = progress;
        });
      });
    } finally {
      if (mounted) {
        setState(() {
          _busy = false;
          _busyMessage = '';
          _busyProgress = null;
        });
      }
    }
  }

  List<RemoteFileEntry> get _visible {
    final q = _search.text.trim().toLowerCase();
    final rows = _items
        .where((item) => q.isEmpty || item.name.toLowerCase().contains(q))
        .toList();

    int compare(RemoteFileEntry a, RemoteFileEntry b) {
      if (a.isDir != b.isDir) return a.isDir ? -1 : 1;
      final res = switch (_sort) {
        FileSort.name => a.name.toLowerCase().compareTo(b.name.toLowerCase()),
        FileSort.modified => a.mtime.compareTo(b.mtime),
        FileSort.size => a.size.compareTo(b.size),
      };
      return _desc ? -res : res;
    }

    rows.sort(compare);
    return rows;
  }

  Map<String, RemoteFileEntry> get _itemByPath {
    final map = <String, RemoteFileEntry>{};
    for (final item in _items) {
      map[item.path] = item;
    }
    return map;
  }

  Future<void> _openOrToggle(RemoteFileEntry item) async {
    if (_selectionMode) {
      _toggleSelection(item.path);
      return;
    }

    if (item.isDir) {
      await _load(item.path);
      return;
    }

    await _showEntryMenu(item);
  }

  void _toggleSelection(String path) {
    setState(() {
      if (_selected.contains(path)) {
        _selected.remove(path);
      } else {
        _selected.add(path);
      }
    });
  }

  Future<void> _showEntryMenu(RemoteFileEntry item) async {
    final s = context.s;
    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (context) {
        final maxHeight = MediaQuery.sizeOf(context).height * 0.82;
        return SafeArea(
          child: ConstrainedBox(
            constraints: BoxConstraints(maxHeight: maxHeight),
            child: SingleChildScrollView(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  ListTile(
                    title: Text(
                      item.name,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    subtitle: Text(
                      item.path,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                  if (item.isDir)
                    ListTile(
                      leading: const Icon(Icons.folder_open_rounded),
                      title: Text(s.openFolder),
                      onTap: () {
                        Navigator.of(context).pop();
                        _load(item.path);
                      },
                    ),
                  ListTile(
                    leading: const Icon(Icons.checklist_rounded),
                    title: Text(s.select),
                    onTap: () {
                      Navigator.of(context).pop();
                      _toggleSelection(item.path);
                    },
                  ),
                  ListTile(
                    leading: const Icon(Icons.copy_rounded),
                    title: Text(s.copy),
                    onTap: () {
                      Navigator.of(context).pop();
                      _setClipboard([item.path], cut: false);
                    },
                  ),
                  ListTile(
                    leading: const Icon(Icons.content_cut_rounded),
                    title: Text(s.cut),
                    onTap: () {
                      Navigator.of(context).pop();
                      _setClipboard([item.path], cut: true);
                    },
                  ),
                  if (_clipboardPaths.isNotEmpty)
                    ListTile(
                      leading: const Icon(Icons.content_paste_rounded),
                      title: Text(s.pasteHere),
                      onTap: () {
                        Navigator.of(context).pop();
                        unawaited(
                          _pasteClipboard(
                            destinationDir: item.isDir ? item.path : _path,
                          ),
                        );
                      },
                    ),
                  if (!item.isDir)
                    ListTile(
                      leading: const Icon(Icons.download_rounded),
                      title: Text(s.downloadLocal),
                      onTap: () {
                        Navigator.of(context).pop();
                        _downloadFiles([item]);
                      },
                    ),
                  if (_canUnpack(item))
                    ListTile(
                      leading: const Icon(Icons.unarchive_rounded),
                      title: Text(s.unpack),
                      onTap: () {
                        Navigator.of(context).pop();
                        unawaited(_unpackEntries([item]));
                      },
                    ),
                  if (!item.isDir)
                    ListTile(
                      leading: const Icon(Icons.sports_esports_rounded),
                      title: Text(s.addToSteam),
                      onTap: () {
                        Navigator.of(context).pop();
                        _addToSteam(item);
                      },
                    ),
                  ListTile(
                    leading: const Icon(Icons.content_copy_rounded),
                    title: Text(s.copyPath),
                    onTap: () {
                      Navigator.of(context).pop();
                      Clipboard.setData(ClipboardData(text: item.path));
                      this.context.toast(s.pathCopied);
                    },
                  ),
                  ListTile(
                    leading: const Icon(Icons.delete_rounded),
                    title: Text(s.delete),
                    onTap: () {
                      Navigator.of(context).pop();
                      _deleteEntries([item]);
                    },
                  ),
                ],
              ),
            ),
          ),
        );
      },
    );
  }

  Future<void> _addToSteam(RemoteFileEntry item) async {
    final s = context.s;
    await _runBusy(s.addingToSteam, () async {
      await widget.client.addToSteam(item.path);
      if (!mounted) return;
      context.toast(s.submittedToSteam);
    });
  }

  Future<void> _downloadFiles(List<RemoteFileEntry> items) async {
    final s = context.s;
    final files = items.where((e) => !e.isDir).toList();
    if (files.isEmpty) {
      context.toast(s.folderDownloadUnsupported);
      return;
    }

    await _runBusy(s.downloading, () async {
      final root = await resolveLocalDownloadDir();
      for (final item in files) {
        final bytes = await widget.client.downloadFile(item.path);
        await saveBytesToLocal(root: root, bytes: bytes, filename: item.name);
      }
      if (!mounted) return;
      context.toast(s.savedTo(root.path));
    });
  }

  Future<void> _downloadSelection() async {
    final map = _itemByPath;
    final items = _selected
        .map((p) => map[p])
        .whereType<RemoteFileEntry>()
        .toList();
    await _downloadFiles(items);
  }

  Future<void> _deleteEntries(List<RemoteFileEntry> items) async {
    final s = context.s;
    if (items.isEmpty) return;

    final confirm = await showDialog<bool>(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: Text(s.confirmDeleteTitle),
          content: Text(s.confirmDeleteMessage(items.length)),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(false),
              child: Text(s.cancel),
            ),
            FilledButton(
              onPressed: () => Navigator.of(context).pop(true),
              child: Text(s.delete),
            ),
          ],
        );
      },
    );

    if (confirm != true) return;

    await _runBusy(s.deleting, () async {
      for (final item in items) {
        await widget.client.deletePath(item.path);
      }
      await _load(_path);
      if (!mounted) return;
      context.toast(s.deleteCompleted);
    });
  }

  Future<void> _deleteSelection() async {
    final map = _itemByPath;
    final items = _selected
        .map((p) => map[p])
        .whereType<RemoteFileEntry>()
        .toList();
    await _deleteEntries(items);
  }

  void _selectAllVisible() {
    final rows = _visible;
    setState(() {
      _selected
        ..clear()
        ..addAll(rows.map((e) => e.path));
    });
  }

  List<RemoteFileEntry> _resolveSelectedItems() {
    final map = _itemByPath;
    return _selected
        .map((path) => map[path])
        .whereType<RemoteFileEntry>()
        .toList();
  }

  String _joinRemotePath(String dir, String name) {
    final normalized = dir.replaceAll('\\', '/').trim();
    final trimmed = normalized.replaceFirst(RegExp(r'/+$'), '');
    if (trimmed.isEmpty || trimmed == '/') return '/$name';
    return '$trimmed/$name';
  }

  bool _isArchiveFile(String name) {
    final lower = name.toLowerCase();
    return lower.endsWith('.zip') ||
        lower.endsWith('.7z') ||
        lower.endsWith('.rar') ||
        lower.endsWith('.tar') ||
        lower.endsWith('.tar.gz') ||
        lower.endsWith('.tar.bz2') ||
        lower.endsWith('.tar.xz') ||
        lower.endsWith('.tgz') ||
        lower.endsWith('.tbz') ||
        lower.endsWith('.tbz2') ||
        lower.endsWith('.txz') ||
        lower.endsWith('.exe');
  }

  bool _canUnpack(RemoteFileEntry item) {
    return !item.isDir && _isArchiveFile(item.name);
  }

  void _setClipboard(List<String> paths, {required bool cut}) {
    final s = context.s;
    final normalized = paths
        .map((path) => path.trim())
        .where((path) => path.isNotEmpty)
        .toSet()
        .toList();
    if (normalized.isEmpty) {
      context.toast(cut ? s.noItemsToCut : s.noItemsToCopy);
      return;
    }
    setState(() {
      _clipboardPaths = normalized;
      _clipboardCut = cut;
    });
    context.toast(
      cut ? s.cutCount(normalized.length) : s.copiedCount(normalized.length),
    );
  }

  Future<void> _copySelection() async {
    final items = _resolveSelectedItems();
    _setClipboard(items.map((item) => item.path).toList(), cut: false);
  }

  Future<void> _cutSelection() async {
    final items = _resolveSelectedItems();
    _setClipboard(items.map((item) => item.path).toList(), cut: true);
  }

  Future<void> _pasteClipboard({String? destinationDir}) async {
    final s = context.s;
    if (_clipboardPaths.isEmpty) {
      context.toast(s.clipboardEmpty);
      return;
    }

    final targetDir = (destinationDir ?? _path).trim();
    final sources = List<String>.from(_clipboardPaths);
    final isCut = _clipboardCut;
    try {
      await _runBusyWithProgress(isCut ? s.moving : s.copying, (update) async {
        for (var i = 0; i < sources.length; i++) {
          final source = sources[i];
          final name = basename(source);
          final destination = _joinRemotePath(targetDir, name);
          if (source == destination) {
            update(
              s.skippedStep(i + 1, sources.length, name),
              progress: (i + 1) / sources.length,
            );
            continue;
          }
          update(
            isCut
                ? s.movingStep(i + 1, sources.length, name)
                : s.copyingStep(i + 1, sources.length, name),
            progress: i / sources.length,
          );
          if (isCut) {
            await widget.client.movePath(
              source: source,
              destination: destination,
            );
          } else {
            await widget.client.copyPath(
              source: source,
              destination: destination,
            );
          }
          update(
            isCut
                ? s.movedStep(i + 1, sources.length, name)
                : s.copiedStep(i + 1, sources.length, name),
            progress: (i + 1) / sources.length,
          );
        }
      });
      if (!mounted) return;
      setState(() {
        _clipboardPaths = const [];
        _clipboardCut = false;
      });
      await _load(_path);
      if (!mounted) return;
      context.toast(isCut ? s.moveCompleted : s.copyCompleted);
    } on ApiException catch (e) {
      if (mounted) context.toast(e.message);
    } catch (_) {
      if (mounted) context.toast(s.pasteFailed);
    }
  }

  Future<void> _unpackEntries(List<RemoteFileEntry> entries) async {
    final s = context.s;
    final targets = entries.where(_canUnpack).toList();
    if (targets.isEmpty) {
      context.toast(s.noArchivesToUnpack);
      return;
    }

    try {
      await _runBusyWithProgress(s.unpacking, (update) async {
        for (var i = 0; i < targets.length; i++) {
          final item = targets[i];
          update(
            s.unpackingStep(i + 1, targets.length, item.name),
            progress: i / targets.length,
          );
          await widget.client.unpackArchive(item.path);
          update(
            s.unpackedStep(i + 1, targets.length, item.name),
            progress: (i + 1) / targets.length,
          );
        }
      });
      if (!mounted) return;
      await _load(_path);
      if (!mounted) return;
      context.toast(s.unpackCompleted);
    } on ApiException catch (e) {
      if (mounted) context.toast(e.message);
    } catch (_) {
      if (mounted) context.toast(s.unpackFailed);
    }
  }

  Future<void> _unpackSelection() async {
    final items = _resolveSelectedItems();
    await _unpackEntries(items);
  }

  String _sortLabel() {
    final s = context.s;
    return switch (_sort) {
      FileSort.name => s.sortSummary(s.sortName, _desc),
      FileSort.modified => s.sortSummary(s.sortDate, _desc),
      FileSort.size => s.sortSummary(s.sortSize, _desc),
    };
  }

  Future<void> _showSearchSheet() async {
    await showModalBottomSheet<void>(
      context: context,
      showDragHandle: true,
      builder: (context) {
        return SafeArea(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextField(
                  controller: _search,
                  autofocus: true,
                  onChanged: (_) => setState(() {}),
                  decoration: InputDecoration(
                    prefixIcon: const Icon(Icons.search_rounded),
                    hintText: context.s.searchHint,
                    suffixIcon: _search.text.isEmpty
                        ? null
                        : IconButton(
                            onPressed: () {
                              setState(() => _search.clear());
                              Navigator.of(context).pop();
                            },
                            icon: const Icon(Icons.close_rounded),
                          ),
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  Future<void> _showSortSheet() async {
    await showModalBottomSheet<void>(
      context: context,
      showDragHandle: true,
      builder: (context) {
        return SafeArea(
          child: StatefulBuilder(
            builder: (context, setModalState) {
              final s = this.context.s;
              void updateSort(FileSort sort) {
                setState(() => _sort = sort);
                setModalState(() {});
              }

              void toggleDirection() {
                setState(() => _desc = !_desc);
                setModalState(() {});
              }

              return Padding(
                padding: const EdgeInsets.fromLTRB(12, 0, 12, 12),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    RadioListTile<FileSort>(
                      value: FileSort.name,
                      groupValue: _sort,
                      onChanged: (value) {
                        if (value != null) updateSort(value);
                      },
                      title: Text(s.sortName),
                    ),
                    RadioListTile<FileSort>(
                      value: FileSort.modified,
                      groupValue: _sort,
                      onChanged: (value) {
                        if (value != null) updateSort(value);
                      },
                      title: Text(s.sortDate),
                    ),
                    RadioListTile<FileSort>(
                      value: FileSort.size,
                      groupValue: _sort,
                      onChanged: (value) {
                        if (value != null) updateSort(value);
                      },
                      title: Text(s.sortSize),
                    ),
                    ListTile(
                      leading: Icon(
                        _desc
                            ? Icons.arrow_downward_rounded
                            : Icons.arrow_upward_rounded,
                      ),
                      title: Text(_desc ? s.sortDescending : s.sortAscending),
                      onTap: toggleDirection,
                    ),
                  ],
                ),
              );
            },
          ),
        );
      },
    );
  }

  Future<String?> _showNameInputDialog({
    required String title,
    required String hint,
  }) async {
    final s = context.s;
    var draft = '';
    final value = await showDialog<String>(
      context: context,
      useRootNavigator: true,
      builder: (dialogContext) {
        return AlertDialog(
          title: Text(title),
          content: TextField(
            autofocus: true,
            onChanged: (value) => draft = value,
            onSubmitted: (value) {
              Navigator.of(
                dialogContext,
                rootNavigator: true,
              ).pop(value.trim());
            },
            decoration: InputDecoration(hintText: hint),
          ),
          actions: [
            TextButton(
              onPressed: () =>
                  Navigator.of(dialogContext, rootNavigator: true).pop(),
              child: Text(s.cancel),
            ),
            FilledButton(
              onPressed: () => Navigator.of(
                dialogContext,
                rootNavigator: true,
              ).pop(draft.trim()),
              child: Text(s.create),
            ),
          ],
        );
      },
    );
    return value?.trim();
  }

  bool _isValidNewName(String value) {
    if (value.trim().isEmpty) return false;
    return !value.contains('/') && !value.contains('\\');
  }

  Future<void> _createFileAction() async {
    final s = context.s;
    final name = await _showNameInputDialog(
      title: s.newFile,
      hint: s.createFileHint,
    );
    if (name == null) return;
    if (!_isValidNewName(name)) {
      context.toast(s.invalidFileName);
      return;
    }
    try {
      await _runBusy(s.creatingFile, () async {
        await widget.client.createFile(path: _path, filename: name);
      });
      if (!mounted) return;
      await _load(_path);
      if (!mounted) return;
      context.toast(s.fileCreated);
    } on ApiException catch (e) {
      if (mounted) context.toast(e.message);
    } catch (_) {
      if (mounted) context.toast(s.createFileFailed);
    }
  }

  Future<void> _createFolderAction() async {
    final s = context.s;
    final name = await _showNameInputDialog(
      title: s.newFolder,
      hint: s.createFolderHint,
    );
    if (name == null) return;
    if (!_isValidNewName(name)) {
      context.toast(s.invalidFolderName);
      return;
    }
    try {
      await _runBusy(s.creatingFolder, () async {
        await widget.client.createDirectory(path: _path, dirname: name);
      });
      if (!mounted) return;
      await _load(_path);
      if (!mounted) return;
      context.toast(s.folderCreated);
    } on ApiException catch (e) {
      if (mounted) context.toast(e.message);
    } catch (_) {
      if (mounted) context.toast(s.createFolderFailed);
    }
  }

  Future<void> _showCreateTypeMenu() async {
    final s = context.s;
    final action = await showModalBottomSheet<String>(
      context: context,
      showDragHandle: true,
      builder: (context) {
        return SafeArea(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              ListTile(
                leading: const Icon(Icons.description_outlined),
                title: Text(s.newFile),
                onTap: () {
                  Navigator.of(context).pop('file');
                },
              ),
              ListTile(
                leading: const Icon(Icons.create_new_folder_rounded),
                title: Text(s.newFolder),
                onTap: () {
                  Navigator.of(context).pop('folder');
                },
              ),
            ],
          ),
        );
      },
    );
    if (!mounted || action == null) return;
    // Let the bottom sheet route finish teardown before pushing dialog route.
    await Future<void>.delayed(const Duration(milliseconds: 16));
    if (!mounted) return;
    if (action == 'file') {
      await _createFileAction();
      return;
    }
    await _createFolderAction();
  }

  Future<void> _showToolsMenu() async {
    final s = context.s;
    final action = await showModalBottomSheet<String>(
      context: context,
      showDragHandle: true,
      builder: (context) {
        return SafeArea(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              ListTile(
                leading: const Icon(Icons.search_rounded),
                title: Text(s.search),
                subtitle: Text(
                  _search.text.trim().isEmpty ? s.notSet : _search.text.trim(),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                onTap: () {
                  Navigator.of(context).pop('search');
                },
              ),
              ListTile(
                leading: const Icon(Icons.sort_rounded),
                title: Text(s.sort),
                subtitle: Text(_sortLabel()),
                onTap: () {
                  Navigator.of(context).pop('sort');
                },
              ),
              ListTile(
                leading: const Icon(Icons.add_box_outlined),
                title: Text(s.newItem),
                onTap: () {
                  Navigator.of(context).pop('new');
                },
              ),
              if (_clipboardPaths.isNotEmpty)
                ListTile(
                  leading: const Icon(Icons.content_paste_rounded),
                  title: Text(
                    _clipboardCut
                        ? '${s.paste} ${_clipboardPaths.length} (${s.cut})'
                        : '${s.paste} ${_clipboardPaths.length}',
                  ),
                  onTap: () {
                    Navigator.of(context).pop('paste');
                  },
                ),
              if (_selectionMode)
                ListTile(
                  leading: const Icon(Icons.select_all_rounded),
                  title: Text(s.selectAllVisible),
                  onTap: () {
                    Navigator.of(context).pop('select-all');
                  },
                ),
              const SizedBox(height: 6),
            ],
          ),
        );
      },
    );
    if (!mounted || action == null) return;
    switch (action) {
      case 'search':
        await _showSearchSheet();
        return;
      case 'sort':
        await _showSortSheet();
        return;
      case 'new':
        await Future<void>.delayed(const Duration(milliseconds: 16));
        if (!mounted) return;
        await _showCreateTypeMenu();
        return;
      case 'paste':
        await _pasteClipboard();
        return;
      case 'select-all':
        _selectAllVisible();
        return;
      default:
        return;
    }
  }

  List<_PathSegment> _segments(String path) {
    final normalized = path.replaceAll('\\', '/');
    final parts = normalized.split('/').where((e) => e.isNotEmpty).toList();
    final segments = <_PathSegment>[
      _PathSegment(label: context.s.rootFolder, path: '/'),
    ];
    var current = '';
    for (final part in parts) {
      current = '$current/$part';
      segments.add(_PathSegment(label: part, path: current));
    }
    return segments;
  }

  @override
  Widget build(BuildContext context) {
    super.build(context);
    final s = context.s;
    final scheme = Theme.of(context).colorScheme;

    return SafeArea(
      bottom: false,
      child: LayoutBuilder(
        builder: (context, constraints) {
          final horizontal = constraints.maxWidth >= 1400
              ? 28.0
              : constraints.maxWidth >= 1000
              ? 20.0
              : constraints.maxWidth >= 760
              ? 24.0
              : 12.0;
          return Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 1320),
              child: Stack(
                children: [
                  Column(
                    children: [
                      Expanded(
                        child: Padding(
                          padding: EdgeInsets.symmetric(horizontal: horizontal),
                          child: RefreshIndicator(
                            onRefresh: () => _load(_path),
                            child: _buildList(),
                          ),
                        ),
                      ),
                      Builder(
                        builder: (context) {
                          final crumbs = _segments(_path);
                          return Container(
                            width: double.infinity,
                            decoration: BoxDecoration(
                              color: scheme.surfaceContainer,
                              borderRadius: const BorderRadius.only(
                                topLeft: Radius.circular(16),
                                topRight: Radius.circular(16),
                              ),
                              border: Border(
                                top: BorderSide(
                                  color: scheme.outlineVariant.withValues(
                                    alpha: 0.35,
                                  ),
                                ),
                              ),
                              boxShadow: [
                                BoxShadow(
                                  color: Colors.black.withValues(alpha: 0.22),
                                  blurRadius: 14,
                                  offset: const Offset(0, -2),
                                ),
                              ],
                            ),
                            padding: EdgeInsets.fromLTRB(
                              horizontal,
                              4,
                              horizontal + 56,
                              4,
                            ),
                            child: SingleChildScrollView(
                              scrollDirection: Axis.horizontal,
                              child: Row(
                                children: [
                                  for (var i = 0; i < crumbs.length; i++) ...[
                                    TextButton(
                                      onPressed:
                                          (_busy || crumbs[i].path == _path)
                                          ? null
                                          : () => _load(crumbs[i].path),
                                      style: TextButton.styleFrom(
                                        padding: const EdgeInsets.symmetric(
                                          horizontal: 8,
                                          vertical: 3,
                                        ),
                                        minimumSize: const Size(0, 32),
                                        tapTargetSize:
                                            MaterialTapTargetSize.shrinkWrap,
                                        foregroundColor:
                                            scheme.onSurfaceVariant,
                                        shape: RoundedRectangleBorder(
                                          borderRadius: BorderRadius.circular(
                                            8,
                                          ),
                                        ),
                                      ),
                                      child: Text(
                                        crumbs[i].label,
                                        style: Theme.of(context)
                                            .textTheme
                                            .bodySmall
                                            ?.copyWith(
                                              fontWeight: FontWeight.w600,
                                              color: crumbs[i].path == _path
                                                  ? scheme.onSurface
                                                  : scheme.onSurfaceVariant
                                                        .withValues(alpha: 0.9),
                                            ),
                                      ),
                                    ),
                                    if (i < crumbs.length - 1)
                                      Padding(
                                        padding: const EdgeInsets.symmetric(
                                          horizontal: 2,
                                        ),
                                        child: Text(
                                          '/',
                                          style: Theme.of(context)
                                              .textTheme
                                              .bodySmall
                                              ?.copyWith(
                                                color: scheme.onSurfaceVariant
                                                    .withValues(alpha: 0.72),
                                              ),
                                        ),
                                      ),
                                  ],
                                ],
                              ),
                            ),
                          );
                        },
                      ),
                      AnimatedSwitcher(
                        duration: const Duration(milliseconds: 180),
                        child: _selectionMode
                            ? Container(
                                key: const ValueKey('file-selection-bar'),
                                width: double.infinity,
                                padding: EdgeInsets.fromLTRB(
                                  horizontal,
                                  6,
                                  horizontal,
                                  4,
                                ),
                                decoration: BoxDecoration(
                                  color: scheme.surfaceContainer,
                                ),
                                child: Row(
                                  children: [
                                    Text(s.selectedCount(_selected.length)),
                                    const SizedBox(width: 8),
                                    Expanded(
                                      child: SingleChildScrollView(
                                        scrollDirection: Axis.horizontal,
                                        child: Row(
                                          mainAxisSize: MainAxisSize.min,
                                          children: [
                                            IconButton(
                                              onPressed: _busy
                                                  ? null
                                                  : _copySelection,
                                              icon: const Icon(
                                                Icons.copy_rounded,
                                              ),
                                              tooltip: s.copy,
                                            ),
                                            IconButton(
                                              onPressed: _busy
                                                  ? null
                                                  : _cutSelection,
                                              icon: const Icon(
                                                Icons.content_cut_rounded,
                                              ),
                                              tooltip: s.cut,
                                            ),
                                            IconButton(
                                              onPressed:
                                                  _busy ||
                                                      _clipboardPaths.isEmpty
                                                  ? null
                                                  : () => unawaited(
                                                      _pasteClipboard(),
                                                    ),
                                              icon: const Icon(
                                                Icons.content_paste_rounded,
                                              ),
                                              tooltip: s.paste,
                                            ),
                                            IconButton(
                                              onPressed: _busy
                                                  ? null
                                                  : _unpackSelection,
                                              icon: const Icon(
                                                Icons.unarchive_rounded,
                                              ),
                                              tooltip: s.unpack,
                                            ),
                                            IconButton(
                                              onPressed: _busy
                                                  ? null
                                                  : _downloadSelection,
                                              icon: const Icon(
                                                Icons.download_rounded,
                                              ),
                                              tooltip: s.downloadLocal,
                                            ),
                                            IconButton(
                                              onPressed: _busy
                                                  ? null
                                                  : _deleteSelection,
                                              icon: const Icon(
                                                Icons.delete_rounded,
                                              ),
                                              tooltip: s.delete,
                                            ),
                                            IconButton(
                                              onPressed: _busy
                                                  ? null
                                                  : () => setState(
                                                      _selected.clear,
                                                    ),
                                              icon: const Icon(
                                                Icons.close_rounded,
                                              ),
                                              tooltip: s.clearSelection,
                                            ),
                                          ],
                                        ),
                                      ),
                                    ),
                                  ],
                                ),
                              )
                            : const SizedBox.shrink(),
                      ),
                    ],
                  ),
                  Positioned(
                    right: horizontal,
                    bottom: _selectionMode ? 96 : 22,
                    child: DecoratedBox(
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        boxShadow: [
                          BoxShadow(
                            color: Colors.black.withValues(alpha: 0.42),
                            blurRadius: 20,
                            offset: const Offset(0, 10),
                          ),
                          BoxShadow(
                            color: scheme.primary.withValues(alpha: 0.24),
                            blurRadius: 22,
                            spreadRadius: -2,
                          ),
                        ],
                      ),
                      child: Material(
                        color: scheme.surfaceContainerHigh.withValues(
                          alpha: 0.96,
                        ),
                        surfaceTintColor: scheme.primary.withValues(
                          alpha: 0.28,
                        ),
                        shape: CircleBorder(
                          side: BorderSide(
                            color: scheme.primary.withValues(alpha: 0.38),
                          ),
                        ),
                        clipBehavior: Clip.antiAlias,
                        child: IconButton(
                          onPressed: _busy ? null : _showToolsMenu,
                          icon: const Icon(Icons.tune_rounded),
                          tooltip: s.more,
                          padding: const EdgeInsets.all(12),
                          constraints: const BoxConstraints.tightFor(
                            width: 50,
                            height: 50,
                          ),
                        ),
                      ),
                    ),
                  ),
                  if (_busy) _buildBusyDialog(context),
                ],
              ),
            ),
          );
        },
      ),
    );
  }

  Widget _buildBusyDialog(BuildContext context) {
    final s = context.s;
    final scheme = Theme.of(context).colorScheme;
    final progress = _busyProgress;
    final percentText = progress == null
        ? null
        : '${(progress * 100).round()}%';

    return Positioned.fill(
      child: AbsorbPointer(
        child: ColoredBox(
          color: Colors.black.withValues(alpha: 0.58),
          child: Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 320),
              child: Material(
                color: scheme.surfaceContainerHigh,
                borderRadius: BorderRadius.circular(24),
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(18, 16, 18, 16),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        s.processing,
                        style: Theme.of(context).textTheme.titleMedium
                            ?.copyWith(fontWeight: FontWeight.w700),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        _busyMessage,
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                          color: scheme.onSurfaceVariant,
                        ),
                      ),
                      const SizedBox(height: 12),
                      LinearProgressIndicator(
                        value: progress,
                        borderRadius: BorderRadius.circular(99),
                      ),
                      if (percentText != null) ...[
                        const SizedBox(height: 8),
                        Text(
                          percentText,
                          style: Theme.of(context).textTheme.labelMedium,
                        ),
                      ],
                    ],
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildList() {
    final s = context.s;
    const topReachSpace = 130.0;
    if (_loading && _items.isEmpty) {
      return ListView(
        children: const [
          SizedBox(height: 220),
          Center(child: CircularProgressIndicator()),
        ],
      );
    }
    if (_error != null) {
      return ListView(
        children: [
          const SizedBox(height: 120),
          Icon(
            Icons.folder_off_rounded,
            size: 54,
            color: Colors.blueGrey.shade300,
          ),
          const SizedBox(height: 10),
          Center(child: Text(_error!)),
          const SizedBox(height: 8),
          Center(
            child: FilledButton.tonal(
              onPressed: () => _load(_path),
              child: Text(s.retry),
            ),
          ),
        ],
      );
    }

    final rows = _visible;
    if (rows.isEmpty) {
      return ListView(
        children: [
          const SizedBox(height: 120),
          Center(child: Text(s.folderEmpty)),
        ],
      );
    }

    final scheme = Theme.of(context).colorScheme;
    return ListView.separated(
      // Keep a reachable black zone above the first row for easier one-hand taps.
      physics: const BouncingScrollPhysics(
        parent: AlwaysScrollableScrollPhysics(),
      ),
      padding: const EdgeInsets.only(top: topReachSpace, bottom: 6),
      itemCount: rows.length,
      separatorBuilder: (context, index) => Divider(
        height: 1,
        thickness: 0.7,
        indent: 64,
        endIndent: 10,
        color: scheme.outlineVariant.withValues(alpha: 0.2),
      ),
      itemBuilder: (context, index) {
        final item = rows[index];
        final selected = _selected.contains(item.path);

        return Material(
          color: selected
              ? scheme.primaryContainer.withValues(alpha: 0.26)
              : Colors.transparent,
          child: ListTile(
            // Dense mode clamps layout and visually limits large SVG icons.
            visualDensity: const VisualDensity(horizontal: -1, vertical: -1),
            minTileHeight: 70,
            minLeadingWidth: 64,
            contentPadding: const EdgeInsets.fromLTRB(10, 6, 6, 6),
            leading: SizedBox(
              width: 51,
              height: 51,
              child: buildFileSystemIcon(
                isDir: item.isDir,
                name: item.name,
                path: item.path,
                fallbackColor: scheme.onSurfaceVariant,
              ),
            ),
            title: Text(
              item.name,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.w600,
              ),
            ),
            subtitle: Text(
              item.isDir
                  ? '${s.folderWord} · ${fmtDate(item.mtime)}'
                  : '${fmtBytes(item.size)} · ${fmtDate(item.mtime)}',
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: scheme.onSurfaceVariant,
              ),
            ),
            trailing: _selectionMode
                ? Icon(
                    selected
                        ? Icons.check_circle_rounded
                        : Icons.radio_button_unchecked_rounded,
                    color: selected ? scheme.primary : scheme.outline,
                  )
                : (item.isDir
                      ? Icon(
                          Icons.chevron_right_rounded,
                          color: scheme.onSurfaceVariant.withValues(alpha: 0.7),
                        )
                      : null),
            onTap: _busy ? null : () => _openOrToggle(item),
            onLongPress: _busy ? null : () => _showEntryMenu(item),
          ),
        );
      },
    );
  }

  @override
  bool get wantKeepAlive => true;
}

class _PathSegment {
  const _PathSegment({required this.label, required this.path});

  final String label;
  final String path;
}

class MediaTab extends StatefulWidget {
  const MediaTab({super.key, required this.client});

  final DeckyApiClient client;

  @override
  State<MediaTab> createState() => _MediaTabState();
}

class _MediaTabState extends State<MediaTab>
    with AutomaticKeepAliveClientMixin<MediaTab> {
  final ScrollController _scroll = ScrollController();
  List<MediaEntry> _items = const [];
  final Set<String> _selected = <String>{};

  bool _loading = false;
  bool _initial = true;
  bool _hasMore = true;
  bool _busy = false;
  int _page = 0;
  String? _error;

  bool get _selectionMode => _selected.isNotEmpty;

  bool clearSelectionForBack() {
    if (_selected.isEmpty) return false;
    setState(() => _selected.clear());
    return true;
  }

  @override
  void initState() {
    super.initState();
    _scroll.addListener(_onScroll);
    unawaited(_refresh());
  }

  @override
  void dispose() {
    _scroll.dispose();
    super.dispose();
  }

  void _onScroll() {
    if (_loading || !_hasMore) return;
    if (_scroll.position.extentAfter < 320) {
      unawaited(_nextPage());
    }
  }

  Future<void> _refresh() async {
    setState(() {
      _items = const [];
      _selected.clear();
      _page = 0;
      _hasMore = true;
      _error = null;
      _initial = true;
    });
    await _nextPage();
  }

  Future<void> _nextPage() async {
    if (_loading || !_hasMore) return;
    setState(() => _loading = true);
    try {
      final data = await widget.client.listMedia(
        page: _page + 1,
        pageSize: 180,
      );
      if (!mounted) return;
      setState(() {
        _items = [..._items, ...data.items];
        _page = data.page;
        _hasMore = data.hasMore;
      });
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.message);
    } catch (_) {
      if (mounted) setState(() => _error = context.s.mediaLoadFailed);
    } finally {
      if (mounted) {
        setState(() {
          _loading = false;
          _initial = false;
        });
      }
    }
  }

  Future<void> _runBusy(Future<void> Function() action) async {
    setState(() => _busy = true);
    try {
      await action();
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  List<MediaEntry> get _visible => _items;

  int _gridCount(double width) {
    if (width >= 1800) return 10;
    if (width >= 1500) return 8;
    if (width >= 1200) return 6;
    if (width >= 900) return 5;
    if (width >= 700) return 4;
    return 3;
  }

  void _toggleSelection(String path) {
    setState(() {
      if (_selected.contains(path)) {
        _selected.remove(path);
      } else {
        _selected.add(path);
      }
    });
  }

  Future<void> _showMediaMenu(MediaEntry item) async {
    final s = context.s;
    final action = await showModalBottomSheet<String>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (context) {
        final maxHeight = MediaQuery.sizeOf(context).height * 0.82;
        return SafeArea(
          child: ConstrainedBox(
            constraints: BoxConstraints(maxHeight: maxHeight),
            child: SingleChildScrollView(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  ListTile(
                    title: Text(
                      item.name,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    subtitle: Text(
                      item.path,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                  ListTile(
                    leading: const Icon(Icons.zoom_out_map_rounded),
                    title: Text(s.preview),
                    onTap: () {
                      Navigator.of(context).pop('preview');
                    },
                  ),
                  ListTile(
                    leading: const Icon(Icons.checklist_rounded),
                    title: Text(s.select),
                    onTap: () {
                      Navigator.of(context).pop('select');
                    },
                  ),
                  ListTile(
                    leading: const Icon(Icons.download_rounded),
                    title: Text(s.downloadLocal),
                    onTap: () {
                      Navigator.of(context).pop('download');
                    },
                  ),
                  ListTile(
                    leading: const Icon(Icons.content_copy_rounded),
                    title: Text(s.copyPath),
                    onTap: () {
                      Navigator.of(context).pop('copy-path');
                    },
                  ),
                ],
              ),
            ),
          ),
        );
      },
    );
    if (!mounted || action == null) return;
    switch (action) {
      case 'preview':
        _showPreview(item);
        return;
      case 'select':
        _toggleSelection(item.path);
        return;
      case 'download':
        await _downloadMedia([item]);
        return;
      case 'copy-path':
        await Clipboard.setData(ClipboardData(text: item.path));
        if (mounted) context.toast(s.pathCopied);
        return;
      default:
        return;
    }
  }

  Future<void> _downloadMedia(List<MediaEntry> items) async {
    final s = context.s;
    if (items.isEmpty) return;

    await _runBusy(() async {
      final root = await resolveLocalDownloadDir();
      for (final item in items) {
        final bytes = await widget.client.downloadMedia(item.path);
        await saveBytesToLocal(root: root, bytes: bytes, filename: item.name);
      }
      if (!mounted) return;
      context.toast(s.savedTo(root.path));
    });
  }

  Future<void> _downloadSelection() async {
    final map = <String, MediaEntry>{
      for (final item in _items) item.path: item,
    };
    final targets = _selected
        .map((path) => map[path])
        .whereType<MediaEntry>()
        .toList();
    await _downloadMedia(targets);
  }

  void _showPreview(MediaEntry item) {
    final s = context.s;
    showGeneralDialog<void>(
      context: context,
      barrierDismissible: true,
      barrierLabel: s.preview,
      barrierColor: Colors.black,
      pageBuilder: (context, animation, secondaryAnimation) {
        final isVideo = item.mediaType == 'video';
        return Scaffold(
          backgroundColor: Colors.black,
          body: Stack(
            fit: StackFit.expand,
            children: [
              if (isVideo)
                Center(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(
                        Icons.play_circle_fill_rounded,
                        color: Colors.white,
                        size: 72,
                      ),
                      const SizedBox(height: 10),
                      Text(
                        item.name,
                        style: const TextStyle(color: Colors.white70),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ],
                  ),
                )
              else
                InteractiveViewer(
                  minScale: 0.6,
                  maxScale: 5,
                  child: Center(
                    child: Image.network(
                      widget.client.previewUri(item.path).toString(),
                      fit: BoxFit.contain,
                      errorBuilder: (context, error, stackTrace) {
                        return const Icon(
                          Icons.broken_image_rounded,
                          size: 64,
                          color: Colors.white70,
                        );
                      },
                    ),
                  ),
                ),
              SafeArea(
                child: Align(
                  alignment: Alignment.topRight,
                  child: Padding(
                    padding: const EdgeInsets.only(top: 8, right: 8),
                    child: IconButton.filledTonal(
                      onPressed: () => Navigator.of(context).pop(),
                      icon: const Icon(Icons.close_rounded),
                      tooltip: s.close,
                    ),
                  ),
                ),
              ),
            ],
          ),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    super.build(context);
    final scheme = Theme.of(context).colorScheme;
    return SafeArea(
      bottom: false,
      child: LayoutBuilder(
        builder: (context, constraints) {
          final desktop = constraints.maxWidth >= 1100;
          final horizontal = constraints.maxWidth >= 1400
              ? 28.0
              : constraints.maxWidth >= 1000
              ? 20.0
              : constraints.maxWidth >= 760
              ? 24.0
              : 12.0;
          return Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 1320),
              child: Column(
                children: [
                  Expanded(
                    child: Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 2),
                      child: _buildBody(),
                    ),
                  ),
                  AnimatedSwitcher(
                    duration: const Duration(milliseconds: 180),
                    switchInCurve: Curves.easeOutCubic,
                    switchOutCurve: Curves.easeInCubic,
                    child: _selectionMode
                        ? desktop
                              ? Container(
                                  key: const ValueKey(
                                    'media-selection-bar-desktop',
                                  ),
                                  margin: EdgeInsets.fromLTRB(
                                    horizontal,
                                    0,
                                    horizontal,
                                    12,
                                  ),
                                  child: Material(
                                    elevation: 1,
                                    shadowColor: Colors.black.withValues(
                                      alpha: 0.16,
                                    ),
                                    surfaceTintColor: Colors.transparent,
                                    color: scheme.surfaceContainer,
                                    shape: RoundedRectangleBorder(
                                      borderRadius: BorderRadius.circular(20),
                                      side: BorderSide(
                                        color: scheme.outlineVariant.withValues(
                                          alpha: 0.3,
                                        ),
                                      ),
                                    ),
                                    clipBehavior: Clip.antiAlias,
                                    child: Column(
                                      mainAxisSize: MainAxisSize.min,
                                      children: [
                                        Padding(
                                          padding: const EdgeInsets.symmetric(
                                            horizontal: 12,
                                          ),
                                          child: Container(
                                            height: 1,
                                            decoration: BoxDecoration(
                                              color: scheme.outlineVariant
                                                  .withValues(alpha: 0.18),
                                              borderRadius:
                                                  BorderRadius.circular(999),
                                            ),
                                          ),
                                        ),
                                        Padding(
                                          padding: const EdgeInsets.symmetric(
                                            horizontal: 14,
                                            vertical: 10,
                                          ),
                                          child: _buildSelectionActions(),
                                        ),
                                      ],
                                    ),
                                  ),
                                )
                              : Material(
                                  key: const ValueKey(
                                    'media-selection-bar-mobile',
                                  ),
                                  elevation: 3,
                                  shadowColor: Colors.black.withValues(
                                    alpha: 0.16,
                                  ),
                                  surfaceTintColor: Colors.transparent,
                                  color: scheme.surfaceContainer,
                                  shape: RoundedRectangleBorder(
                                    borderRadius: BorderRadius.only(
                                      topLeft: Radius.circular(24),
                                      topRight: Radius.circular(24),
                                    ),
                                    side: BorderSide(
                                      color: scheme.outlineVariant.withValues(
                                        alpha: 0.3,
                                      ),
                                    ),
                                  ),
                                  clipBehavior: Clip.antiAlias,
                                  child: Column(
                                    mainAxisSize: MainAxisSize.min,
                                    children: [
                                      Padding(
                                        padding: const EdgeInsets.symmetric(
                                          horizontal: 12,
                                        ),
                                        child: Container(
                                          height: 1,
                                          decoration: BoxDecoration(
                                            color: scheme.outlineVariant
                                                .withValues(alpha: 0.18),
                                            borderRadius: BorderRadius.circular(
                                              999,
                                            ),
                                          ),
                                        ),
                                      ),
                                      Padding(
                                        padding: const EdgeInsets.fromLTRB(
                                          14,
                                          10,
                                          14,
                                          12,
                                        ),
                                        child: _buildSelectionActions(),
                                      ),
                                    ],
                                  ),
                                )
                        : SizedBox(
                            key: ValueKey<String>(
                              desktop
                                  ? 'media-selection-empty-desktop'
                                  : 'media-selection-empty-mobile',
                            ),
                            height: desktop ? 12 : 0,
                          ),
                  ),
                ],
              ),
            ),
          );
        },
      ),
    );
  }

  Widget _buildSelectionActions() {
    final s = context.s;
    return Row(
      children: [
        Text(s.selectedCount(_selected.length)),
        const Spacer(),
        IconButton(
          onPressed: _busy ? null : _downloadSelection,
          icon: const Icon(Icons.download_rounded),
          tooltip: s.downloadLocal,
        ),
        IconButton(
          onPressed: _busy
              ? null
              : () {
                  final visible = _visible;
                  setState(() {
                    _selected
                      ..clear()
                      ..addAll(visible.map((e) => e.path));
                  });
                },
          icon: const Icon(Icons.select_all_rounded),
          tooltip: s.selectAllVisible,
        ),
        IconButton(
          onPressed: _busy ? null : () => setState(_selected.clear),
          icon: const Icon(Icons.close_rounded),
          tooltip: s.clearSelection,
        ),
      ],
    );
  }

  Widget _buildBody() {
    final s = context.s;
    if (_initial) {
      return const Center(child: CircularProgressIndicator());
    }
    if (_error != null && _items.isEmpty) {
      return ListView(
        children: [
          const SizedBox(height: 140),
          Center(child: Text(_error!)),
        ],
      );
    }

    final rows = _visible;
    if (rows.isEmpty) {
      return RefreshIndicator(
        onRefresh: _refresh,
        child: ListView(
          physics: const AlwaysScrollableScrollPhysics(),
          children: [
            const SizedBox(height: 160),
            Center(child: Text(s.noMedia)),
          ],
        ),
      );
    }

    return LayoutBuilder(
      builder: (context, constraints) {
        return RefreshIndicator(
          onRefresh: _refresh,
          child: GridView.builder(
            controller: _scroll,
            physics: const AlwaysScrollableScrollPhysics(),
            reverse: true,
            padding: const EdgeInsets.only(bottom: 12),
            gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: _gridCount(constraints.maxWidth),
              mainAxisSpacing: 1,
              crossAxisSpacing: 1,
              childAspectRatio: 1,
            ),
            itemCount: rows.length + (_loading ? 1 : 0),
            itemBuilder: (context, index) {
              if (index >= rows.length) {
                return const Card(
                  child: Center(child: CircularProgressIndicator()),
                );
              }

              final item = rows[index];
              final selected = _selected.contains(item.path);

              return Material(
                color: Colors.transparent,
                child: InkWell(
                  onTap: _busy
                      ? null
                      : () {
                          if (_selectionMode) {
                            _toggleSelection(item.path);
                          } else {
                            _showMediaMenu(item);
                          }
                        },
                  onLongPress: _busy ? null : () => _toggleSelection(item.path),
                  child: Ink(
                    decoration: BoxDecoration(
                      color: Theme.of(context).colorScheme.surfaceContainerLow,
                    ),
                    child: Stack(
                      fit: StackFit.expand,
                      children: [
                        if (item.mediaType == 'image')
                          Image.network(
                            widget.client.previewUri(item.path).toString(),
                            fit: BoxFit.cover,
                            errorBuilder: (context, error, stackTrace) {
                              return Container(
                                color: const Color(0xFF121519),
                                child: const Icon(
                                  Icons.image_not_supported_rounded,
                                  color: Colors.white70,
                                ),
                              );
                            },
                          )
                        else
                          const DecoratedBox(
                            decoration: BoxDecoration(
                              gradient: LinearGradient(
                                begin: Alignment.topLeft,
                                end: Alignment.bottomRight,
                                colors: [Color(0xFF0E557A), Color(0xFF2C8DA5)],
                              ),
                            ),
                            child: Center(
                              child: Icon(
                                Icons.play_circle_fill_rounded,
                                color: Colors.white,
                                size: 44,
                              ),
                            ),
                          ),
                        if (selected)
                          Positioned.fill(
                            child: Container(
                              decoration: BoxDecoration(
                                border: Border.all(
                                  color: Theme.of(context).colorScheme.primary,
                                  width: 2,
                                ),
                              ),
                            ),
                          ),
                        if (_selectionMode || selected)
                          Positioned(
                            top: 6,
                            right: 6,
                            child: Container(
                              width: 24,
                              height: 24,
                              decoration: BoxDecoration(
                                color: Colors.black.withValues(alpha: 0.36),
                                borderRadius: BorderRadius.circular(999),
                              ),
                              child: Icon(
                                selected
                                    ? Icons.check_circle_rounded
                                    : Icons.radio_button_unchecked_rounded,
                                color: selected ? Colors.white : Colors.white70,
                                size: 18,
                              ),
                            ),
                          ),
                      ],
                    ),
                  ),
                ),
              );
            },
          ),
        );
      },
    );
  }

  @override
  bool get wantKeepAlive => true;
}

class TextTab extends StatefulWidget {
  const TextTab({super.key, required this.client});

  final DeckyApiClient client;

  @override
  State<TextTab> createState() => _TextTabState();
}

class _TextTabState extends State<TextTab>
    with AutomaticKeepAliveClientMixin<TextTab> {
  final TextEditingController _text = TextEditingController();
  final FocusNode _focus = FocusNode();
  bool _sending = false;
  static const int _maxChars = 12000;

  bool get _canSend => _text.text.trim().isNotEmpty && !_sending;
  int get _charCount => _text.text.length;

  @override
  void initState() {
    super.initState();
    _text.addListener(_onInputStateChanged);
    _focus.addListener(_onInputStateChanged);
  }

  void _onInputStateChanged() {
    if (mounted) {
      setState(() {});
    }
  }

  @override
  void dispose() {
    _text.removeListener(_onInputStateChanged);
    _focus.removeListener(_onInputStateChanged);
    _text.dispose();
    _focus.dispose();
    super.dispose();
  }

  Future<void> _send() async {
    final s = context.s;
    final value = _text.text.trim();
    if (value.isEmpty) {
      context.toast(s.inputTextFirst);
      return;
    }

    setState(() => _sending = true);
    try {
      await widget.client.uploadText(value);
      if (!mounted) return;
      context.toast(s.textSent);
      _text.clear();
      _focus.unfocus();
    } on ApiException catch (e) {
      if (mounted) context.toast(e.message);
    } catch (_) {
      if (mounted) context.toast(s.textUploadFailed);
    } finally {
      if (mounted) setState(() => _sending = false);
    }
  }

  Future<void> _paste() async {
    final data = await Clipboard.getData('text/plain');
    final text = data?.text ?? '';
    setState(() {
      _text.text = text;
      _text.selection = TextSelection.collapsed(offset: _text.text.length);
    });
  }

  @override
  Widget build(BuildContext context) {
    super.build(context);
    final scheme = Theme.of(context).colorScheme;
    final keyboardInset = MediaQuery.viewInsetsOf(context).bottom;
    const dockHeight = 76.0;

    return SafeArea(
      bottom: false,
      child: LayoutBuilder(
        builder: (context, constraints) {
          final desktop = constraints.maxWidth >= 1100;
          if (desktop) {
            return Padding(
              padding: const EdgeInsets.fromLTRB(16, 16, 16, 14),
              child: Row(
                children: [
                  Expanded(
                    child: Container(
                      decoration: BoxDecoration(
                        color: Colors.black,
                        borderRadius: BorderRadius.circular(24),
                      ),
                      child: Stack(
                        children: [
                          Positioned.fill(child: _buildTextEditor(context)),
                          Positioned(
                            top: 10,
                            right: 10,
                            child: _buildCounterChip(context),
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(width: 16),
                  SizedBox(
                    width: 340,
                    child: _buildTextDock(context, desktop: true),
                  ),
                ],
              ),
            );
          }

          return Stack(
            children: [
              Positioned.fill(
                child: Padding(
                  padding: EdgeInsets.fromLTRB(
                    0,
                    0,
                    0,
                    dockHeight + keyboardInset,
                  ),
                  child: AnimatedContainer(
                    duration: const Duration(milliseconds: 220),
                    curve: Curves.easeOutCubic,
                    decoration: const BoxDecoration(color: Colors.black),
                    child: Stack(
                      children: [
                        Positioned.fill(child: _buildTextEditor(context)),
                        Positioned(
                          top: 10,
                          right: 10,
                          child: _buildCounterChip(context),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
              Positioned(
                left: 0,
                right: 0,
                bottom: keyboardInset,
                child: _buildTextDock(context),
              ),
            ],
          );
        },
      ),
    );
  }

  Widget _buildCounterChip(BuildContext context) {
    final theme = Theme.of(context);
    final scheme = theme.colorScheme;
    return AnimatedOpacity(
      duration: const Duration(milliseconds: 180),
      opacity: _focus.hasFocus || _charCount > 0 ? 1 : 0.72,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(999),
          color: scheme.secondaryContainer.withValues(alpha: 0.86),
        ),
        child: Text(
          '$_charCount/$_maxChars',
          style: theme.textTheme.labelMedium?.copyWith(
            color: scheme.onSecondaryContainer,
            fontWeight: FontWeight.w700,
          ),
        ),
      ),
    );
  }

  Widget _buildTextEditor(BuildContext context) {
    final theme = Theme.of(context);
    final scheme = theme.colorScheme;
    return TextField(
      controller: _text,
      focusNode: _focus,
      expands: true,
      minLines: null,
      maxLines: null,
      maxLength: _maxChars,
      textAlignVertical: TextAlignVertical.top,
      style: theme.textTheme.bodyLarge?.copyWith(
        height: 1.45,
        fontWeight: FontWeight.w500,
      ),
      decoration: InputDecoration(
        filled: true,
        fillColor: Colors.black,
        counterText: '',
        hintText: context.s.textInputHint,
        hintStyle: theme.textTheme.bodyLarge?.copyWith(
          color: scheme.onSurfaceVariant.withValues(alpha: 0.72),
        ),
        border: InputBorder.none,
        contentPadding: const EdgeInsets.fromLTRB(16, 16, 16, 16),
      ),
    );
  }

  Widget _buildTextDock(BuildContext context, {bool desktop = false}) {
    final scheme = Theme.of(context).colorScheme;
    return Material(
      elevation: desktop ? 1 : 3,
      shadowColor: Colors.black.withValues(alpha: 0.16),
      surfaceTintColor: Colors.transparent,
      color: scheme.surfaceContainer,
      shape: RoundedRectangleBorder(
        borderRadius: desktop
            ? BorderRadius.circular(24)
            : const BorderRadius.only(
                topLeft: Radius.circular(24),
                topRight: Radius.circular(24),
              ),
        side: BorderSide(
          color: scheme.outlineVariant.withValues(alpha: desktop ? 0.42 : 0.3),
        ),
      ),
      clipBehavior: Clip.antiAlias,
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            height: 1,
            width: double.infinity,
            color: scheme.outlineVariant.withValues(alpha: 0.34),
          ),
          Padding(
            padding: const EdgeInsets.fromLTRB(12, 10, 12, 12),
            child: desktop
                ? Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Row(
                        children: [
                          Expanded(
                            child: SizedBox(
                              height: 44,
                              child: FilledButton.tonal(
                                onPressed: _sending ? null : _paste,
                                child: const Icon(Icons.content_paste_rounded),
                              ),
                            ),
                          ),
                          const SizedBox(width: 8),
                          Expanded(
                            child: SizedBox(
                              height: 44,
                              child: OutlinedButton(
                                onPressed: _sending
                                    ? null
                                    : () => setState(() => _text.clear()),
                                child: const Icon(Icons.clear_rounded),
                              ),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 10),
                      SizedBox(
                        height: 48,
                        child: FilledButton.icon(
                          onPressed: _canSend ? _send : null,
                          icon: AnimatedSwitcher(
                            duration: const Duration(milliseconds: 200),
                            child: _sending
                                ? const SizedBox(
                                    key: ValueKey('sending'),
                                    width: 16,
                                    height: 16,
                                    child: CircularProgressIndicator(
                                      strokeWidth: 2,
                                    ),
                                  )
                                : const Icon(
                                    Icons.send_rounded,
                                    key: ValueKey('send'),
                                  ),
                          ),
                          label: Text(
                            _sending
                                ? context.s.sendingText
                                : context.s.sendText,
                          ),
                        ),
                      ),
                    ],
                  )
                : Row(
                    children: [
                      Expanded(
                        child: SizedBox(
                          height: 44,
                          child: FilledButton.tonal(
                            onPressed: _sending ? null : _paste,
                            child: const Icon(Icons.content_paste_rounded),
                          ),
                        ),
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: SizedBox(
                          height: 44,
                          child: OutlinedButton(
                            onPressed: _sending
                                ? null
                                : () => setState(() => _text.clear()),
                            child: const Icon(Icons.clear_rounded),
                          ),
                        ),
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        flex: 2,
                        child: SizedBox(
                          height: 44,
                          child: FilledButton.icon(
                            onPressed: _canSend ? _send : null,
                            icon: AnimatedSwitcher(
                              duration: const Duration(milliseconds: 200),
                              child: _sending
                                  ? const SizedBox(
                                      key: ValueKey('sending'),
                                      width: 16,
                                      height: 16,
                                      child: CircularProgressIndicator(
                                        strokeWidth: 2,
                                      ),
                                    )
                                  : const Icon(
                                      Icons.send_rounded,
                                      key: ValueKey('send'),
                                    ),
                            ),
                            label: Text(
                              _sending
                                  ? context.s.sendingText
                                  : context.s.sendText,
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),
          ),
        ],
      ),
    );
  }

  @override
  bool get wantKeepAlive => true;
}

class QrScanScreen extends StatefulWidget {
  const QrScanScreen({super.key});

  @override
  State<QrScanScreen> createState() => _QrScanScreenState();
}

class _QrScanScreenState extends State<QrScanScreen> {
  final MobileScannerController _controller = MobileScannerController(
    formats: const [BarcodeFormat.qrCode],
  );
  bool _done = false;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _onDetect(BarcodeCapture capture) {
    if (_done) return;
    if (capture.barcodes.isEmpty) return;
    final value = capture.barcodes.first.rawValue?.trim();
    if (value == null || value.isEmpty) return;

    final endpoint = parseEndpointFromQr(value);
    if (endpoint == null) {
      context.toast(context.s.invalidQrPayload);
      return;
    }

    _done = true;
    Navigator.of(context).pop(endpoint);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Stack(
        fit: StackFit.expand,
        children: [
          MobileScanner(controller: _controller, onDetect: _onDetect),
          Center(
            child: Container(
              width: 250,
              height: 250,
              decoration: BoxDecoration(
                border: Border.all(color: Colors.white, width: 3),
                borderRadius: BorderRadius.circular(18),
              ),
            ),
          ),
          SafeArea(
            child: Align(
              alignment: Alignment.topRight,
              child: Padding(
                padding: const EdgeInsets.only(top: 8, right: 8),
                child: IconButton.filledTonal(
                  onPressed: () => Navigator.of(context).pop(),
                  icon: const Icon(Icons.close_rounded),
                  tooltip: context.s.close,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class DeckyEndpoint {
  const DeckyEndpoint({required this.host, required this.port});

  final String host;
  final int port;

  String get baseUrl => 'http://$host:$port';
  String get label => '$host:$port';

  Map<String, dynamic> toJson() => {'host': host, 'port': port};

  static DeckyEndpoint? fromJson(dynamic raw) {
    if (raw is! Map<String, dynamic>) return null;
    final host = (raw['host'] as String?)?.trim() ?? '';
    final port = raw['port'] is int
        ? raw['port'] as int
        : int.tryParse('${raw['port']}');
    if (host.isEmpty || port == null || port <= 0 || port > 65535) return null;
    return DeckyEndpoint(host: host, port: port);
  }
}

class AppBootstrap {
  const AppBootstrap({required this.initial, required this.recent});

  final DeckyEndpoint? initial;
  final List<DeckyEndpoint> recent;
}

class LocalStore {
  static const _keyHost = 'decky_host';
  static const _keyPort = 'decky_port';
  static const _keyRecent = 'decky_recent_endpoints';

  static Future<AppBootstrap> load() async {
    final prefs = await SharedPreferences.getInstance();
    final host = (prefs.getString(_keyHost) ?? '').trim();
    final port = prefs.getInt(_keyPort);
    final initial = host.isNotEmpty && port != null
        ? DeckyEndpoint(host: host, port: port)
        : null;

    final raw = prefs.getStringList(_keyRecent) ?? const [];
    final recent = <DeckyEndpoint>[];
    for (final item in raw) {
      try {
        final endpoint = DeckyEndpoint.fromJson(jsonDecode(item));
        if (endpoint != null) recent.add(endpoint);
      } catch (_) {
        continue;
      }
    }

    final seeds = initial == null
        ? recent
        : <DeckyEndpoint>[initial, ...recent];
    return AppBootstrap(initial: initial, recent: dedupe(seeds));
  }

  static Future<void> savePrimary(DeckyEndpoint endpoint) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_keyHost, endpoint.host);
    await prefs.setInt(_keyPort, endpoint.port);
  }

  static Future<void> pushRecent(DeckyEndpoint endpoint) async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getStringList(_keyRecent) ?? const [];
    final recent = <DeckyEndpoint>[endpoint];
    for (final item in raw) {
      try {
        final parsed = DeckyEndpoint.fromJson(jsonDecode(item));
        if (parsed != null) recent.add(parsed);
      } catch (_) {
        continue;
      }
    }
    final merged = dedupe(
      recent,
    ).take(8).map((e) => jsonEncode(e.toJson())).toList();
    await prefs.setStringList(_keyRecent, merged);
  }
}

class DeckyApiClient {
  DeckyApiClient(this.endpoint, {http.Client? client})
    : _client = client ?? http.Client();

  final DeckyEndpoint endpoint;
  final http.Client _client;

  Uri _uri(String path, [Map<String, String>? query]) {
    final uri = Uri.parse('${endpoint.baseUrl}$path');
    return query == null ? uri : uri.replace(queryParameters: query);
  }

  Future<Map<String, dynamic>> _json(http.Response response) async {
    final body = utf8.decode(response.bodyBytes);
    Map<String, dynamic> data;
    try {
      final decoded = jsonDecode(body);
      data = decoded is Map<String, dynamic> ? decoded : <String, dynamic>{};
    } catch (_) {
      data = {};
    }

    if (response.statusCode < 200 || response.statusCode >= 300) {
      final msg = (data['message'] as String?)?.trim();
      throw ApiException(
        msg?.isNotEmpty == true
            ? msg!
            : 'Request failed (${response.statusCode})',
      );
    }
    if (data['status'] == 'error') {
      throw ApiException('${data['message'] ?? 'Server error'}');
    }
    return data;
  }

  Future<UploadOptions> fetchUploadOptions() async {
    final response = await _client.get(_uri('/api/settings/upload-options'));
    final data = await _json(response);
    return UploadOptions(
      defaultDir: data['default_dir'] as String?,
      promptUploadPath: data['prompt_upload_path'] == true,
    );
  }

  Future<ListFilesResult> listFiles({required String path}) async {
    final response = await _client.post(
      _uri('/api/files/list'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'path': path}),
    );
    final data = await _json(response);
    final raw = data['files'] as List<dynamic>? ?? const [];
    return ListFilesResult(
      currentPath: (data['current_path'] as String?)?.trim().isNotEmpty == true
          ? data['current_path'] as String
          : '/',
      files: raw.map(RemoteFileEntry.fromJson).toList(),
    );
  }

  Future<void> createFile({
    required String path,
    required String filename,
  }) async {
    final response = await _client.post(
      _uri('/api/files/create'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'path': path, 'filename': filename}),
    );
    await _json(response);
  }

  Future<void> createDirectory({
    required String path,
    required String dirname,
  }) async {
    final response = await _client.post(
      _uri('/api/files/create-dir'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'path': path, 'dirname': dirname}),
    );
    await _json(response);
  }

  Future<void> copyPath({
    required String source,
    required String destination,
  }) async {
    final response = await _client.post(
      _uri('/api/files/copy'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'source': source, 'destination': destination}),
    );
    await _json(response);
  }

  Future<void> movePath({
    required String source,
    required String destination,
  }) async {
    final response = await _client.post(
      _uri('/api/files/move'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'source': source, 'destination': destination}),
    );
    await _json(response);
  }

  Future<void> unpackArchive(String path) async {
    final response = await _client.post(
      _uri('/api/files/unpack'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'path': path}),
    );
    await _json(response);
  }

  Future<MediaPage> listMedia({required int page, int pageSize = 200}) async {
    final response = await _client.get(
      _uri('/api/media/list', {'page': '$page', 'page_size': '$pageSize'}),
    );
    final data = await _json(response);
    final raw = data['items'] as List<dynamic>? ?? const [];
    return MediaPage(
      items: raw.map(MediaEntry.fromJson).toList(),
      page: data['page'] is int ? data['page'] as int : page,
      hasMore: data['has_more'] == true,
    );
  }

  Uri previewUri(String path) => _uri('/api/media/preview', {'path': path});

  Future<void> uploadFile({required String filePath, String? destPath}) async {
    final file = File(filePath);
    if (!await file.exists()) {
      throw const ApiException('Local file not found');
    }

    final request = http.MultipartRequest('POST', _uri('/upload'));
    if (destPath != null && destPath.trim().isNotEmpty) {
      request.fields['dest_path'] = destPath.trim();
    }
    request.files.add(
      await http.MultipartFile.fromPath(
        'file',
        file.path,
        filename: basename(file.path),
      ),
    );

    final streamed = await _client.send(request);
    final response = await http.Response.fromStream(streamed);
    await _json(response);
  }

  Future<void> deletePath(String path) async {
    final response = await _client.post(
      _uri('/api/files/delete'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'path': path}),
    );
    await _json(response);
  }

  Future<void> addToSteam(String path) async {
    final response = await _client.post(
      _uri('/api/files/add-to-steam'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'path': path}),
    );
    await _json(response);
  }

  Future<List<int>> downloadFile(String path) async {
    return _downloadBytes(_uri('/api/files/download', {'path': path}));
  }

  Future<List<int>> downloadMedia(String path) async {
    return _downloadBytes(_uri('/api/files/download', {'path': path}));
  }

  Future<List<int>> _downloadBytes(Uri uri) async {
    final response = await _client.get(uri);
    if (response.statusCode >= 200 && response.statusCode < 300) {
      return response.bodyBytes;
    }

    try {
      final body = utf8.decode(response.bodyBytes);
      final decoded = jsonDecode(body);
      if (decoded is Map<String, dynamic>) {
        final message = (decoded['message'] as String?)?.trim();
        throw ApiException(
          message?.isNotEmpty == true
              ? message!
              : 'Request failed (${response.statusCode})',
        );
      }
    } catch (_) {
      // Fall through to generic error.
    }
    throw ApiException('Request failed (${response.statusCode})');
  }

  Future<void> uploadText(String text) async {
    final response = await _client.post(
      _uri('/upload-text'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'text': text}),
    );
    await _json(response);
  }

  void dispose() {
    _client.close();
  }
}

class UploadOptions {
  const UploadOptions({
    required this.defaultDir,
    required this.promptUploadPath,
  });

  final String? defaultDir;
  final bool promptUploadPath;
}

class ListFilesResult {
  const ListFilesResult({required this.currentPath, required this.files});

  final String currentPath;
  final List<RemoteFileEntry> files;
}

class RemoteFileEntry {
  const RemoteFileEntry({
    required this.name,
    required this.path,
    required this.isDir,
    required this.size,
    required this.mtime,
  });

  final String name;
  final String path;
  final bool isDir;
  final int size;
  final double mtime;

  static RemoteFileEntry fromJson(dynamic raw) {
    final map = raw is Map<String, dynamic> ? raw : <String, dynamic>{};
    return RemoteFileEntry(
      name: '${map['name'] ?? ''}',
      path: '${map['path'] ?? ''}',
      isDir: map['is_dir'] == true,
      size: map['size'] is int
          ? map['size'] as int
          : int.tryParse('${map['size']}') ?? 0,
      mtime: map['mtime'] is num
          ? (map['mtime'] as num).toDouble()
          : double.tryParse('${map['mtime']}') ?? 0,
    );
  }
}

class MediaEntry {
  const MediaEntry({
    required this.name,
    required this.path,
    required this.size,
    required this.mtime,
    required this.mediaType,
  });

  final String name;
  final String path;
  final int size;
  final double mtime;
  final String mediaType;

  static MediaEntry fromJson(dynamic raw) {
    final map = raw is Map<String, dynamic> ? raw : <String, dynamic>{};
    return MediaEntry(
      name: '${map['name'] ?? ''}',
      path: '${map['path'] ?? ''}',
      size: map['size'] is int
          ? map['size'] as int
          : int.tryParse('${map['size']}') ?? 0,
      mtime: map['mtime'] is num
          ? (map['mtime'] as num).toDouble()
          : double.tryParse('${map['mtime']}') ?? 0,
      mediaType: '${map['media_type'] ?? 'image'}',
    );
  }
}

class MediaPage {
  const MediaPage({
    required this.items,
    required this.page,
    required this.hasMore,
  });

  final List<MediaEntry> items;
  final int page;
  final bool hasMore;
}

class ApiException implements Exception {
  const ApiException(this.message);

  final String message;
}

class AppStrings {
  const AppStrings(this.locale);

  final Locale locale;

  bool get isZh => locale.languageCode.toLowerCase().startsWith('zh');

  static AppStrings of(BuildContext context) {
    final locale =
        Localizations.maybeLocaleOf(context) ??
        WidgetsBinding.instance.platformDispatcher.locale;
    return AppStrings(locale);
  }

  String get navTransfer => isZh ? '传输' : 'Transfer';
  String get navFiles => isZh ? '文件' : 'Files';
  String get navMedia => isZh ? '媒体' : 'Media';
  String get navText => isZh ? '文本' : 'Text';
  String get backAgainToExit =>
      isZh ? '再按一次返回退出应用' : 'Press back again to exit';

  String get connectIntro => isZh
      ? '通过接口端点连接并管理文件与媒体。'
      : 'Connect and manage files and media via API endpoint.';
  String get hostLabel => isZh ? '主机地址' : 'Host';
  String get portLabel => isZh ? '端口' : 'Port';
  String get connect => isZh ? '连接' : 'Connect';
  String get connecting => isZh ? '连接中...' : 'Connecting...';
  String get scanQr => isZh ? '扫码连接' : 'Scan QR';
  String get detectLan => isZh ? '检测局域网' : 'Detect LAN';
  String get recentEndpoints => isZh ? '最近连接' : 'Recent endpoints';
  String get invalidHostOrPort => isZh ? '主机或端口无效' : 'Invalid host or port';
  String get connectionFailed => isZh ? '连接失败' : 'Connection failed';
  String get lanIpUnavailable => isZh
      ? '无法读取本机 IP，请确认已连接 Wi-Fi。'
      : 'Cannot read local IP. Ensure Wi-Fi is connected.';
  String lanHintWithIp(String ip) => isZh
      ? '手机 IP：$ip，请填写同网段 Steam Deck 的 IP。'
      : 'Phone IP: $ip. Use Steam Deck IP in same subnet.';

  String get fileManager => isZh ? '文件管理' : 'File Manager';
  String get rootFolder => isZh ? '根目录' : 'Root';
  String itemsCount(int value) => isZh ? '$value 项' : '$value items';
  String get more => isZh ? '更多' : 'More';
  String get search => isZh ? '搜索' : 'Search';
  String get sort => isZh ? '排序' : 'Sort';
  String get newItem => isZh ? '新建' : 'New';
  String get notSet => isZh ? '未设置' : 'Not set';
  String get searchHint => isZh ? '搜索当前目录' : 'Search current folder';
  String searchActive(String value) => isZh ? '搜索：$value' : 'Search: $value';
  String get sortName => isZh ? '名称' : 'Name';
  String get sortDate => isZh ? '日期' : 'Date';
  String get sortSize => isZh ? '大小' : 'Size';
  String get sortDescending => isZh ? '降序' : 'Descending';
  String get sortAscending => isZh ? '升序' : 'Ascending';
  String sortSummary(String field, bool desc) => isZh
      ? '$field · ${desc ? '降序' : '升序'}'
      : '$field · ${desc ? 'desc' : 'asc'}';
  String get newFile => isZh ? '新建文件' : 'New file';
  String get newFolder => isZh ? '新建文件夹' : 'New folder';
  String get create => isZh ? '创建' : 'Create';
  String get cancel => isZh ? '取消' : 'Cancel';
  String get close => isZh ? '关闭' : 'Close';
  String get clear => isZh ? '清空' : 'Clear';

  String get openFolder => isZh ? '打开文件夹' : 'Open folder';
  String get select => isZh ? '选择' : 'Select';
  String get copy => isZh ? '复制' : 'Copy';
  String get cut => isZh ? '剪切' : 'Cut';
  String get paste => isZh ? '粘贴' : 'Paste';
  String get pasteHere => isZh ? '粘贴到这里' : 'Paste here';
  String get unpack => isZh ? '解压' : 'Unpack';
  String get downloadLocal => isZh ? '下载到本地' : 'Download to local';
  String get addToSteam => isZh ? '添加到 Steam' : 'Add to Steam';
  String get copyPath => isZh ? '复制路径' : 'Copy path';
  String get pathCopied => isZh ? '路径已复制' : 'Path copied';
  String get delete => isZh ? '删除' : 'Delete';
  String get preview => isZh ? '预览' : 'Preview';
  String get clearSelection => isZh ? '清空选择' : 'Clear selection';
  String selectedCount(int count) => isZh ? '已选择 $count 项' : 'Selected $count';
  String get selectAllVisible => isZh ? '全选当前可见项' : 'Select all visible';

  String get noItemsToCopy => isZh ? '没有可复制的项目' : 'No items to copy';
  String get noItemsToCut => isZh ? '没有可剪切的项目' : 'No items to cut';
  String copiedCount(int count) =>
      isZh ? '已复制 $count 项' : 'Copied $count item(s)';
  String cutCount(int count) => isZh ? '已剪切 $count 项' : 'Cut $count item(s)';
  String get clipboardEmpty => isZh ? '剪贴板为空' : 'Clipboard is empty';
  String get moving => isZh ? '正在移动...' : 'Moving...';
  String get copying => isZh ? '正在复制...' : 'Copying...';
  String movingStep(int index, int total, String name) =>
      isZh ? '移动 $index/$total · $name' : 'Moving $index/$total · $name';
  String copyingStep(int index, int total, String name) =>
      isZh ? '复制 $index/$total · $name' : 'Copying $index/$total · $name';
  String movedStep(int index, int total, String name) =>
      isZh ? '已移动 $index/$total · $name' : 'Moved $index/$total · $name';
  String copiedStep(int index, int total, String name) =>
      isZh ? '已复制 $index/$total · $name' : 'Copied $index/$total · $name';
  String skippedStep(int index, int total, String name) =>
      isZh ? '已跳过 $index/$total · $name' : 'Skipped $index/$total · $name';
  String get moveCompleted => isZh ? '移动完成' : 'Move completed';
  String get copyCompleted => isZh ? '复制完成' : 'Copy completed';
  String get pasteFailed => isZh ? '粘贴失败' : 'Paste failed';

  String get noArchivesToUnpack => isZh ? '没有可解压的压缩包' : 'No archives to unpack';
  String get unpacking => isZh ? '正在解压...' : 'Unpacking...';
  String unpackingStep(int index, int total, String name) =>
      isZh ? '解压 $index/$total · $name' : 'Unpacking $index/$total · $name';
  String unpackedStep(int index, int total, String name) =>
      isZh ? '已解压 $index/$total · $name' : 'Unpacked $index/$total · $name';
  String get unpackCompleted => isZh ? '解压完成' : 'Unpack completed';
  String get unpackFailed => isZh ? '解压失败' : 'Unpack failed';

  String get invalidFileName => isZh ? '文件名无效' : 'Invalid file name';
  String get invalidFolderName => isZh ? '文件夹名无效' : 'Invalid folder name';
  String get createFileHint => isZh ? '例如：example.txt' : 'example.txt';
  String get createFolderHint => isZh ? '新建文件夹' : 'New Folder';
  String get creatingFile => isZh ? '正在创建文件...' : 'Creating file...';
  String get creatingFolder => isZh ? '正在创建文件夹...' : 'Creating folder...';
  String get fileCreated => isZh ? '文件已创建' : 'File created';
  String get folderCreated => isZh ? '文件夹已创建' : 'Folder created';
  String get createFileFailed => isZh ? '创建文件失败' : 'Create file failed';
  String get createFolderFailed => isZh ? '创建文件夹失败' : 'Create folder failed';

  String get addingToSteam => isZh ? '正在添加到 Steam...' : 'Adding to Steam...';
  String get submittedToSteam => isZh ? '已提交到 Steam' : 'Submitted to Steam';
  String get folderDownloadUnsupported =>
      isZh ? '文件夹不支持直接下载' : 'Folders cannot be downloaded directly';
  String get downloading => isZh ? '正在下载...' : 'Downloading...';
  String savedTo(String path) => isZh ? '已保存到 $path' : 'Saved to $path';

  String get confirmDeleteTitle => isZh ? '确认删除' : 'Confirm delete';
  String confirmDeleteMessage(int count) =>
      isZh ? '确认删除选中的 $count 项吗？' : 'Delete $count selected item(s)?';
  String get deleting => isZh ? '正在删除...' : 'Deleting...';
  String get deleteCompleted => isZh ? '删除完成' : 'Delete completed';
  String get retry => isZh ? '重试' : 'Retry';
  String get folderEmpty => isZh ? '当前文件夹为空' : 'Folder is empty';
  String get folderWord => isZh ? '文件夹' : 'Folder';
  String get processing => isZh ? '处理中' : 'Processing';
  String get directoryLoadFailed => isZh ? '目录加载失败' : 'Directory load failed';
  String get selectedFiles => isZh ? '已选文件' : 'Selected files';
  String get noSelectedFiles => isZh ? '暂无已选文件' : 'No selected files';
  String get transferStackHint => isZh
      ? '文件列表将从传输栏上方向上堆叠显示'
      : 'Files will stack upward from the transfer dock';
  String get selectFilesFirst => isZh ? '请先选择文件' : 'Select files first';
  String get pickFiles => isZh ? '选择文件' : 'Pick files';
  String get chooseUploadPathFirst =>
      isZh ? '请先选择传输路径' : 'Please choose an upload destination first';
  String get chooseUploadPathTitle => isZh ? '选择传输路径' : 'Choose destination';
  String uploadPathCurrent(String path) =>
      isZh ? '当前路径：$path' : 'Current path: $path';
  String get selectCurrentFolder => isZh ? '选择当前文件夹' : 'Use current folder';
  String get upLevel => isZh ? '上一级' : 'Up';
  String get noSubfolders =>
      isZh ? '当前目录没有子文件夹' : 'No subfolders in current folder';
  String get uploadPathLoadFailed =>
      isZh ? '读取目录失败' : 'Failed to read directory';
  String get startUpload => isZh ? '开始上传' : 'Start upload';
  String get uploading => isZh ? '上传中...' : 'Uploading...';
  String uploadProgress(int current, int total, String name) =>
      isZh ? '上传 $current/$total · $name' : 'Uploading $current/$total · $name';
  String get uploadCompleted => isZh ? '上传完成' : 'Upload completed';
  String get uploadFailed => isZh ? '上传失败' : 'Upload failed';

  String get mediaLoadFailed => isZh ? '媒体加载失败' : 'Media load failed';
  String get noMedia => isZh ? '暂无媒体文件' : 'No media files';

  String get inputTextFirst => isZh ? '请先输入文本' : 'Input text first';
  String get textSent => isZh ? '文本已发送' : 'Text sent';
  String get textUploadFailed => isZh ? '文本发送失败' : 'Text upload failed';
  String get textInputHint => isZh ? '请输入或粘贴文本' : 'Type or paste text';
  String get sendText => isZh ? '发送文本' : 'Send text';
  String get sendingText => isZh ? '发送中...' : 'Sending...';
  String get invalidQrPayload => isZh ? '二维码内容无效' : 'Invalid QR payload';
}

extension BuildStrings on BuildContext {
  AppStrings get s => AppStrings.of(this);
}

extension BuildToast on BuildContext {
  void toast(String message) {
    ScaffoldMessenger.of(this).showSnackBar(SnackBar(content: Text(message)));
  }
}

DeckyEndpoint? parseEndpointFromQr(String value) {
  final text = value.trim();
  if (text.isEmpty) return null;

  final uri = Uri.tryParse(text);
  if (uri != null && uri.host.isNotEmpty) {
    return DeckyEndpoint(
      host: uri.host,
      port: uri.hasPort ? uri.port : kDefaultPort,
    );
  }

  if (text.startsWith('{') && text.endsWith('}')) {
    try {
      return DeckyEndpoint.fromJson(jsonDecode(text));
    } catch (_) {
      return null;
    }
  }

  final match = RegExp(r'^([A-Za-z0-9\.\-_]+):(\d{1,5})$').firstMatch(text);
  if (match == null) return null;
  final host = match.group(1)!;
  final port = int.tryParse(match.group(2)!);
  if (port == null || port <= 0 || port > 65535) return null;
  return DeckyEndpoint(host: host, port: port);
}

List<DeckyEndpoint> dedupe(List<DeckyEndpoint> list) {
  final out = <DeckyEndpoint>[];
  final seen = <String>{};
  for (final item in list) {
    final key = '${item.host}:${item.port}';
    if (seen.add(key)) out.add(item);
  }
  return out;
}

String parentPath(String path) {
  final normalized = path.replaceAll('\\', '/').trim();
  if (normalized.isEmpty || normalized == '/') return '/';
  final parts = normalized.split('/').where((p) => p.isNotEmpty).toList();
  if (parts.isEmpty) return '/';
  parts.removeLast();
  return parts.isEmpty ? '/' : '/${parts.join('/')}';
}

const _kIconRoot = 'assets/tubiaobao';
const _kMimeRoot = '$_kIconRoot/mimetypes';
const _kPlaceRoot = '$_kIconRoot/places';

Widget buildFileSystemIcon({
  required bool isDir,
  required String name,
  String? path,
  Color? fallbackColor,
}) {
  final asset = isDir
      ? folderIconAsset(path: path ?? name)
      : fileIconAsset(name: name, path: path);
  final fallback = isDir
      ? Icons.folder_rounded
      : Icons.insert_drive_file_rounded;

  return SvgPicture.asset(
    asset,
    fit: BoxFit.contain,
    placeholderBuilder: (context) =>
        Icon(fallback, size: 33, color: fallbackColor),
  );
}

String folderIconAsset({required String path}) {
  final normalized = path.replaceAll('\\', '/').toLowerCase();
  final folderName = basename(path).toLowerCase();
  bool hasToken(String token) =>
      folderName.contains(token) || normalized.contains('/$token');

  if (hasToken('network-server') || hasToken('server')) {
    return '$_kPlaceRoot/network-server.svg';
  }
  if (hasToken('workgroup')) {
    return '$_kPlaceRoot/network-workgroup.svg';
  }
  if (hasToken('trash') || hasToken('recycle') || hasToken('bin')) {
    return '$_kPlaceRoot/user-trash.svg';
  }
  if (hasToken('desktop')) {
    return '$_kPlaceRoot/user-desktop.svg';
  }
  if (hasToken('bookmark')) {
    return '$_kPlaceRoot/user-bookmarks.svg';
  }
  if (normalized == '/home' || normalized == '/home/deck') {
    return '$_kPlaceRoot/folder-drag-accept.svg';
  }
  if (hasToken('download')) {
    return '$_kPlaceRoot/folder-download.svg';
  }
  if (hasToken('document') || folderName == 'docs' || folderName == 'doc') {
    return '$_kPlaceRoot/folder-documents.svg';
  }
  if (hasToken('music') || hasToken('audio')) {
    return '$_kPlaceRoot/folder-music.svg';
  }
  if (hasToken('picture') ||
      hasToken('photo') ||
      hasToken('dcim') ||
      hasToken('image')) {
    return '$_kPlaceRoot/folder-pictures.svg';
  }
  if (hasToken('video') || hasToken('movie') || hasToken('film')) {
    return '$_kPlaceRoot/folder-videos.svg';
  }
  if (hasToken('public') || hasToken('share')) {
    return '$_kPlaceRoot/folder-publicshare.svg';
  }
  if (hasToken('template')) {
    return '$_kPlaceRoot/folder-templates.svg';
  }
  if (hasToken('remote') ||
      hasToken('smb') ||
      hasToken('ftp') ||
      hasToken('nfs')) {
    return '$_kPlaceRoot/folder-remote.svg';
  }
  if (hasToken('incoming') || hasToken('drop')) {
    return '$_kPlaceRoot/folder-drag-accept.svg';
  }
  if (folderName.startsWith('.')) {
    return '$_kMimeRoot/inode-directory.svg';
  }
  return '$_kPlaceRoot/folder-drag-accept.svg';
}

String fileIconAsset({required String name, String? path}) {
  final lowerName = name.toLowerCase();
  final extIndex = lowerName.lastIndexOf('.');
  final ext = extIndex >= 0 ? lowerName.substring(extIndex + 1) : '';
  final fullPath = (path ?? '').toLowerCase();

  const imageExts = {
    'png',
    'jpg',
    'jpeg',
    'gif',
    'webp',
    'bmp',
    'tif',
    'tiff',
    'heic',
    'heif',
    'svg',
    'ico',
  };
  const videoExts = {
    'mp4',
    'mkv',
    'mov',
    'avi',
    'wmv',
    'flv',
    'm4v',
    'webm',
    '3gp',
  };
  const audioExts = {'mp3', 'flac', 'wav', 'aac', 'ogg', 'm4a', 'opus', 'wma'};
  const fontExts = {'ttf', 'otf', 'woff', 'woff2', 'eot'};
  const textExts = {
    'txt',
    'json',
    'yaml',
    'yml',
    'toml',
    'ini',
    'cfg',
    'conf',
    'xml',
    'log',
    'properties',
    'gradle',
    'lock',
  };
  const scriptExts = {
    'sh',
    'bash',
    'zsh',
    'bat',
    'cmd',
    'ps1',
    'py',
    'js',
    'mjs',
    'cjs',
    'ts',
    'tsx',
    'java',
    'kt',
    'kts',
    'dart',
    'go',
    'rs',
    'lua',
    'rb',
    'pl',
    'swift',
    'php',
    'c',
    'cpp',
    'h',
    'hpp',
    'cs',
  };
  const packageExts = {
    'zip',
    '7z',
    'rar',
    'tar',
    'gz',
    'bz2',
    'xz',
    'tgz',
    'tbz',
    'tbz2',
    'txz',
    'apk',
    'aab',
    'deb',
    'rpm',
    'pkg',
    'ipa',
  };

  if (ext == 'lnk' || ext == 'desktop' || ext == 'url') {
    return '$_kMimeRoot/inode-symlink.svg';
  }
  if (ext == 'pem' ||
      ext == 'cer' ||
      ext == 'crt' ||
      ext == 'p12' ||
      ext == 'pfx' ||
      ext == 'csr' ||
      ext == 'key') {
    return '$_kMimeRoot/application-certificate.svg';
  }
  if (ext == 'exe' || ext == 'bin' || ext == 'run' || ext == 'appimage') {
    return '$_kMimeRoot/application-x-executable.svg';
  }
  if (ext == 'dll' || ext == 'so' || ext == 'dylib') {
    return '$_kMimeRoot/application-x-sharedlib.svg';
  }
  if (ext == 'fw' || ext == 'rom' || ext == 'img' || ext == 'iso') {
    return '$_kMimeRoot/application-x-firmware.svg';
  }
  if (ext == 'addon' || ext == 'plugin' || ext == 'pak' || ext == 'mod') {
    return '$_kMimeRoot/application-x-addon.svg';
  }
  if (packageExts.contains(ext)) {
    return '$_kMimeRoot/package-x-generic.svg';
  }
  if (ext == 'repo' || ext == 'sources' || fullPath.endsWith('.sources.list')) {
    return '$_kMimeRoot/x-package-repository.svg';
  }
  if (ext == 'vcf') {
    return '$_kMimeRoot/x-office-addressbook.svg';
  }
  if (ext == 'dot' || ext == 'dotx' || ext == 'ott' || ext == 'dotm') {
    return '$_kMimeRoot/x-office-document-template.svg';
  }
  if (ext == 'doc' || ext == 'docx' || ext == 'odt' || ext == 'rtf' || ext == 'pdf') {
    return '$_kMimeRoot/x-office-document.svg';
  }
  if (ext == 'xlt' || ext == 'xltx' || ext == 'ots' || ext == 'xltm') {
    return '$_kMimeRoot/x-office-spreadsheet-template.svg';
  }
  if (ext == 'xls' || ext == 'xlsx' || ext == 'ods' || ext == 'csv' || ext == 'tsv') {
    return '$_kMimeRoot/x-office-spreadsheet.svg';
  }
  if (ext == 'pot' || ext == 'potx' || ext == 'otp' || ext == 'potm') {
    return '$_kMimeRoot/x-office-presentation-template.svg';
  }
  if (ext == 'ppt' || ext == 'pptx' || ext == 'odp' || ext == 'key') {
    return '$_kMimeRoot/x-office-presentation.svg';
  }
  if (ext == 'drawio' ||
      ext == 'ai' ||
      ext == 'cdr' ||
      ext == 'psd' ||
      ext == 'xcf' ||
      ext == 'sketch') {
    return '$_kMimeRoot/x-office-drawing.svg';
  }
  if (ext == 'obj' ||
      ext == 'fbx' ||
      ext == 'stl' ||
      ext == 'gltf' ||
      ext == 'glb' ||
      ext == '3ds' ||
      ext == 'blend' ||
      ext == 'dae') {
    return '$_kMimeRoot/model.svg';
  }
  if (ext == 'html' || ext == 'htm' || ext == 'xhtml') {
    return '$_kMimeRoot/text-html.svg';
  }
  if (scriptExts.contains(ext)) {
    return '$_kMimeRoot/text-x-script.svg';
  }
  if (ext == 'md' || ext == 'markdown' || ext == 'rst' || ext == 'adoc') {
    return '$_kMimeRoot/text-x-preview.svg';
  }
  if (textExts.contains(ext)) {
    return '$_kMimeRoot/text-x-generic.svg';
  }
  if (imageExts.contains(ext)) {
    return '$_kMimeRoot/image-x-generic.svg';
  }
  if (videoExts.contains(ext)) {
    return '$_kMimeRoot/video-x-generic.svg';
  }
  if (audioExts.contains(ext)) {
    return '$_kMimeRoot/audio-x-generic.svg';
  }
  if (fontExts.contains(ext)) {
    return '$_kMimeRoot/font-x-generic.svg';
  }
  return '$_kMimeRoot/application-x-generic.svg';
}

String fmtBytes(int bytes) {
  if (bytes <= 0) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  final value = log(bytes) / log(1024);
  final index = value.floor().clamp(0, units.length - 1);
  final sized = bytes / pow(1024, index);
  if (index == 0) return '${sized.toStringAsFixed(0)} ${units[index]}';
  return '${sized.toStringAsFixed(sized >= 10 ? 1 : 2)} ${units[index]}';
}

String fmtDate(double epochSeconds) {
  if (epochSeconds <= 0) return '-';
  final dt = DateTime.fromMillisecondsSinceEpoch(
    (epochSeconds * 1000).toInt(),
  ).toLocal();
  String p(int v) => v.toString().padLeft(2, '0');
  return '${dt.year}-${p(dt.month)}-${p(dt.day)} ${p(dt.hour)}:${p(dt.minute)}';
}

Future<Directory> resolveLocalDownloadDir() async {
  Directory? output;

  try {
    output = await getDownloadsDirectory();
  } catch (_) {
    output = null;
  }

  if (output == null && Platform.isAndroid) {
    try {
      output = await getExternalStorageDirectory();
    } catch (_) {
      output = null;
    }
  }

  output ??= await getApplicationDocumentsDirectory();
  if (!await output.exists()) {
    await output.create(recursive: true);
  }
  return output;
}

Future<File> saveBytesToLocal({
  required Directory root,
  required List<int> bytes,
  required String filename,
}) async {
  final safe = sanitizeFilename(filename);
  final rootPath = root.path;
  final basePath = joinPath(rootPath, safe);
  var output = File(basePath);

  if (await output.exists()) {
    final extIndex = safe.lastIndexOf('.');
    final stem = extIndex > 0 ? safe.substring(0, extIndex) : safe;
    final ext = extIndex > 0 ? safe.substring(extIndex) : '';
    var index = 1;
    while (await output.exists()) {
      output = File(joinPath(rootPath, '$stem ($index)$ext'));
      index++;
    }
  }

  await output.parent.create(recursive: true);
  await output.writeAsBytes(bytes, flush: true);
  return output;
}

String joinPath(String base, String child) {
  if (base.isEmpty) return child;
  if (child.isEmpty) return base;
  final normalizedBase = base
      .replaceAll('\\', '/')
      .replaceFirst(RegExp(r'/+$'), '');
  final normalizedChild = child
      .replaceAll('\\', '/')
      .replaceFirst(RegExp(r'^/+'), '');
  return '$normalizedBase/$normalizedChild';
}

String basename(String path) {
  final normalized = path.replaceAll('\\', '/');
  final parts = normalized.split('/');
  return parts.isEmpty ? path : parts.last;
}

String sanitizeFilename(String raw) {
  final trimmed = raw.trim();
  final source = trimmed.isEmpty ? 'download' : trimmed;
  final cleaned = source
      .replaceAll(RegExp(r'[<>:"/\\|?*\x00-\x1F]'), '_')
      .replaceAll(RegExp(r'\s+'), ' ');
  final finalName = cleaned.trim();
  return finalName.isEmpty ? 'download' : finalName;
}
