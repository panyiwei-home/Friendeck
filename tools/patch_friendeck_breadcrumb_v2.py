from pathlib import Path


TARGET = Path(r"G:\proj\Decky-send\friendeck\lib\main.dart")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f"Missing block: {label}")
    return text.replace(old, new, 1)


def main() -> None:
    raw = TARGET.read_text(encoding="utf-8")
    nl = "\r\n" if "\r\n" in raw else "\n"
    text = raw.replace("\r\n", "\n")

    if "bool get _canNavigateUp => _normalizePath(_path) != '/';" not in text:
        text = replace_once(
            text,
            "  bool get _selectionMode => _selected.isNotEmpty;\n",
            "  bool get _selectionMode => _selected.isNotEmpty;\n"
            "  bool get _canNavigateUp => _normalizePath(_path) != '/';\n",
            "add canNavigateUp getter",
        )

    if "Future<void> _navigateUp() async {" not in text:
        text = replace_once(
            text,
            """  List<_PathSegment> _segments(String path) {
    final normalized = path.replaceAll('\\\\', '/');
    final parts = normalized.split('/').where((e) => e.isNotEmpty).toList();
    final segments = <_PathSegment>[
      const _PathSegment(label: 'Root', path: '/'),
    ];
    var current = '';
    for (final part in parts) {
      current = '$current/$part';
      segments.add(_PathSegment(label: part, path: current));
    }
    return segments;
  }
""",
            """  String _normalizePath(String value) {
    final normalized = value.replaceAll('\\\\', '/').trim();
    if (normalized.isEmpty || normalized == '/') return '/';
    return normalized.replaceAll(RegExp(r'/+$'), '');
  }

  Future<void> _navigateUp() async {
    final current = _normalizePath(_path);
    if (current == '/') return;
    String parent;
    try {
      parent = _normalizePath(Directory(current).parent.path);
    } catch (_) {
      parent = _normalizePath(parentPath(current));
    }
    if (parent == current || parent.isEmpty) {
      parent = '/';
    }
    await _load(parent);
  }

  List<_PathSegment> _segments(String path) {
    final normalized = _normalizePath(path);
    if (normalized == '/') {
      return const [_PathSegment(label: '/', path: '/')];
    }
    final parts = normalized.split('/').where((e) => e.isNotEmpty).toList();
    final segments = <_PathSegment>[const _PathSegment(label: '/', path: '/')];
    var current = '';
    for (final part in parts) {
      current = '$current/$part';
      segments.add(_PathSegment(label: part, path: current));
    }
    return segments;
  }
""",
            "replace path helpers",
        )

    if "icon: const Icon(Icons.chevron_left_rounded)" not in text:
        text = replace_once(
            text,
            """                            Row(
                              children: [
                                Text(
                                  'File Manager',
                                  style: Theme.of(context).textTheme.titleMedium
                                      ?.copyWith(fontWeight: FontWeight.w800),
                                ),
                                const Spacer(),
""",
            """                            Row(
                              children: [
                                IconButton(
                                  onPressed: (_busy || !_canNavigateUp)
                                      ? null
                                      : _navigateUp,
                                  icon: const Icon(Icons.chevron_left_rounded),
                                  tooltip: 'Back',
                                  visualDensity: VisualDensity.compact,
                                ),
                                Text(
                                  'File Manager',
                                  style: Theme.of(context).textTheme.titleMedium
                                      ?.copyWith(fontWeight: FontWeight.w800),
                                ),
                                const Spacer(),
""",
            "add header back button",
        )

    if "FilterChip(" in text:
        text = replace_once(
            text,
            """                            const SizedBox(height: 10),
                            SingleChildScrollView(
                              scrollDirection: Axis.horizontal,
                              child: Row(
                                children: _segments(_path)
                                    .map(
                                      (s) => Padding(
                                        padding: const EdgeInsets.only(
                                          right: 6,
                                        ),
                                        child: FilterChip(
                                          label: Text(s.label),
                                          selected: s.path == _path,
                                          onSelected: (_) {
                                            if (s.path != _path) {
                                              _load(s.path);
                                            }
                                          },
                                        ),
                                      ),
                                    )
                                    .toList(),
                              ),
                            ),
                            const SizedBox(height: 8),
""",
            """                            const SizedBox(height: 8),
""",
            "remove top breadcrumb chips",
        )

    if "padding: EdgeInsets.fromLTRB(horizontal, 2, horizontal, 4)," not in text:
        text = replace_once(
            text,
            """                  Expanded(
                    child: Padding(
                      padding: EdgeInsets.symmetric(horizontal: horizontal),
                      child: RefreshIndicator(
                        onRefresh: () => _load(_path),
                        child: _buildList(),
                      ),
                    ),
                  ),
                  AnimatedSwitcher(
""",
            """                  Expanded(
                    child: Padding(
                      padding: EdgeInsets.symmetric(horizontal: horizontal),
                      child: RefreshIndicator(
                        onRefresh: () => _load(_path),
                        child: _buildList(),
                      ),
                    ),
                  ),
                  Padding(
                    padding: EdgeInsets.fromLTRB(horizontal, 2, horizontal, 4),
                    child: Builder(
                      builder: (context) {
                        final crumbs = _segments(_path);
                        return Container(
                          decoration: BoxDecoration(
                            color: scheme.surfaceContainer,
                            borderRadius: BorderRadius.circular(14),
                          ),
                          padding: const EdgeInsets.symmetric(
                            horizontal: 6,
                            vertical: 4,
                          ),
                          child: Align(
                            alignment: Alignment.centerLeft,
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
                                          horizontal: 10,
                                          vertical: 8,
                                        ),
                                        minimumSize: const Size(0, 40),
                                        tapTargetSize:
                                            MaterialTapTargetSize.padded,
                                        foregroundColor:
                                            scheme.onSurfaceVariant,
                                        shape: RoundedRectangleBorder(
                                          borderRadius: BorderRadius.circular(
                                            10,
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
                          ),
                        );
                      },
                    ),
                  ),
                  AnimatedSwitcher(
""",
            "add bottom breadcrumb bar",
        )
    else:
        # If bottom breadcrumb already exists, only update its style/touch target.
        text = text.replace(
            "color: scheme.surfaceContainerHigh,",
            "color: scheme.surfaceContainer,",
            1,
        )
        text = text.replace(
            "padding: const EdgeInsets.symmetric(\n"
            "                                        horizontal: 4,\n"
            "                                        vertical: 0,\n"
            "                                      ),\n"
            "                                      minimumSize: Size.zero,\n"
            "                                      tapTargetSize:\n"
            "                                          MaterialTapTargetSize.shrinkWrap,",
            "padding: const EdgeInsets.symmetric(\n"
            "                                        horizontal: 10,\n"
            "                                        vertical: 8,\n"
            "                                      ),\n"
            "                                      minimumSize: const Size(0, 40),\n"
            "                                      tapTargetSize:\n"
            "                                          MaterialTapTargetSize.padded,",
            1,
        )

    TARGET.write_text(text.replace("\n", nl), encoding="utf-8")
    print("patched")


if __name__ == "__main__":
    main()
