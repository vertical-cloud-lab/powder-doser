include <threaded-storage-auger-core.scad>;
difference() {
    threaded_storage_cap();
    translate([-50,-50,-5]) cube([100,50,60]);
}
