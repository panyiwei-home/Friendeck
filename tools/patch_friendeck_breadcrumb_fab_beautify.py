from pathlib import Path

path = Path(r"G:\proj\Decky-send\friendeck\lib\main.dart")
text = path.read_text(encoding="utf-8")

# 1) Remove top breadcrumb chips block.
old_top = """                                const SizedBox(height: 10),
                                SingleChildScrollView(
                                  scrollDirection: Axis.horizontal,
                                  child: Row(
                                    children: _segments(_path)
                                        .map(
                                          (segment) => Padding(
                                            padding: const EdgeInsets.only(
                                              right: 6,
                                            ),
                                            child: FilterChip(
                                              label: Text(segment.label),
                                              selected: segment.path == _path,
                                              onSelected: (_) {
                                                if (segment.path != _path) {
                                                  _load(segment.path);
                                                }
                                              },
                                            ),
                                          ),
                                        )
                                        .toList(),
                                  ),
                                ),
"""
if old_top not in text:
    raise SystemExit("top breadcrumb block not found")
text = text.replace(old_top, "                                const SizedBox(height: 8),\n", 1)

# 2) Insert redesigned bottom breadcrumb bar above selection bar.
old_mid = """                      const SizedBox(height: 10),
                      Expanded(
                        child: Padding(
                          padding: EdgeInsets.symmetric(horizontal: horizontal),
                          child: RefreshIndicator(
                            onRefresh: () => _load(_path),
                            child: _buildList(),
                          ),
                        ),
                      ),
                      AnimatedSwitcher(
"""
new_mid = """                      const SizedBox(height: 10),
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
                              gradient: LinearGradient(
                                begin: Alignment.topLeft,
                                end: Alignment.bottomRight,
                                colors: [
                                  scheme.surfaceContainerHigh.withValues(alpha: 0.95),
                                  scheme.surfaceContainer.withValues(alpha: 0.92),
                                ],
                              ),
                              borderRadius: const BorderRadius.only(
                                topLeft: Radius.circular(16),
                                topRight: Radius.circular(16),
                              ),
                              border: Border(
                                top: BorderSide(
                                  color: scheme.outlineVariant.withValues(alpha: 0.35),
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
                                        foregroundColor: scheme.onSurfaceVariant,
                                        shape: RoundedRectangleBorder(
                                          borderRadius: BorderRadius.circular(8),
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
"""
if old_mid not in text:
    raise SystemExit("insert point for bottom breadcrumb not found")
text = text.replace(old_mid, new_mid, 1)

# 3) Make floating options button a circular glass control and slightly higher.
old_fab = """                  Positioned(
                    right: horizontal,
                    bottom: _selectionMode ? 92 : 18,
                    child: DecoratedBox(
                      decoration: BoxDecoration(
                        borderRadius: BorderRadius.circular(18),
                        boxShadow: [
                          BoxShadow(
                            color: Colors.black.withValues(alpha: 0.42),
                            blurRadius: 18,
                            offset: const Offset(0, 8),
                          ),
                          BoxShadow(
                            color: scheme.primary.withValues(alpha: 0.22),
                            blurRadius: 20,
                            spreadRadius: -2,
                          ),
                        ],
                      ),
                      child: Material(
                        color: scheme.surfaceContainerHigh.withValues(
                          alpha: 0.96,
                        ),
                        surfaceTintColor: scheme.primary.withValues(alpha: 0.28),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(18),
                          side: BorderSide(
                            color: scheme.primary.withValues(alpha: 0.35),
                          ),
                        ),
                        child: IconButton(
                          onPressed: _busy ? null : _showToolsMenu,
                          icon: const Icon(Icons.tune_rounded),
                          tooltip: s.more,
                        ),
                      ),
                    ),
                  ),
"""
new_fab = """                  Positioned(
                    right: horizontal,
                    bottom: _selectionMode ? 104 : 30,
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
                        color: scheme.surfaceContainerHigh.withValues(alpha: 0.96),
                        surfaceTintColor: scheme.primary.withValues(alpha: 0.28),
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
"""
if old_fab not in text:
    raise SystemExit("floating button block not found")
text = text.replace(old_fab, new_fab, 1)

# 4) Remove idle spacer gap below selection bar.
text = text.replace(": const SizedBox(height: 12),", ": const SizedBox.shrink(),", 1)

path.write_text(text, encoding="utf-8")
print("patched")
