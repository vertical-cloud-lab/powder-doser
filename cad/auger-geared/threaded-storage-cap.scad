// ================================================================
// Powder Excavator -- Hand-operated screw-on CAP for the threaded
// storage augers
// ================================================================
//
// Asked for by @swcharles on PR #49 (comment 4720626775): a simple
// cap with an internal thread that screws onto the threaded storage
// auger to seal the filling (top "+") end -- "like a long bottle cap".
//
//   * Internal thread matches the external thread on
//     threaded_archimedes-auger-storage.scad and
//     threaded_archimedes-auger-storage-test.scad (one cap fits both --
//     the thread profile is identical on both augers).
//   * Threaded engagement ~1 inch (thread_len from the core file).
//   * Top outer edge is chamfered "because it looks good".
//   * The cap is larger in diameter than the auger (allowed by the
//     request); only the AUGER thread is constrained to the auger OD.
//
// Render:
//   openscad -o threaded-storage-cap.stl threaded-storage-cap.scad
// ================================================================

include <threaded-storage-auger-core.scad>;

threaded_storage_cap();
