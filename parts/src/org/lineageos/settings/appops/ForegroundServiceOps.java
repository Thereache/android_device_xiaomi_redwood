/*
 * SPDX-License-Identifier: Apache-2.0
 */

package org.lineageos.settings.appops;

import android.app.AppOpsManager;
import android.content.Context;
import android.util.Log;

import java.util.List;

public final class ForegroundServiceOps {
    private static final String TAG = "ForegroundServiceOps";
    private static final String OP_START_FOREGROUND = "android:start_foreground";

    private ForegroundServiceOps() {}

    public static void restore(Context context) {
        final AppOpsManager appOps = context.getSystemService(AppOpsManager.class);
        int restored = 0;
        try {
            final List<AppOpsManager.PackageOps> packages =
                    appOps.getPackagesForOps(new String[] {OP_START_FOREGROUND});
            for (AppOpsManager.PackageOps packageOps : packages) {
                for (AppOpsManager.OpEntry entry : packageOps.getOps()) {
                    if (entry.getMode() != AppOpsManager.MODE_IGNORED) {
                        continue;
                    }
                    appOps.setMode(OP_START_FOREGROUND, packageOps.getUid(),
                            packageOps.getPackageName(), AppOpsManager.MODE_ALLOWED);
                    restored++;
                }
            }
        } catch (RuntimeException e) {
            Log.e(TAG, "Failed to restore the foreground service app op", e);
        }
        if (restored > 0) {
            Log.i(TAG, "Allowed foreground services for " + restored + " packages");
        }
    }
}
