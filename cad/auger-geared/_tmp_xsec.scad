include <threaded-storage-auger-core.scad>;
difference() {
    intersection() {
        threaded_archimedes_auger_storage(total_h=90, with_gear=false);
        translate([-50,-50,55]) cube([100,100,40]);
    }
    translate([-50,-50,50]) cube([100,50,50]); // remove y<0 half, keep y>0
}
