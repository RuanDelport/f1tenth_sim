import numpy as np 
import matplotlib.pyplot as plt
import os
from f1tenth_benchmarks.data_tools.plotting_utils import *
from matplotlib.collections import LineCollection
import trajectory_planning_helpers as tph

def ensure_path_exists(path):
    if not os.path.exists(path): 
        os.mkdir(path)

def render_mpcc_plans(planner_name, test_id, map_name="aut"):
    root = f"Logs/{planner_name}/"
    mpcc_data_path = root + f"RawData_{test_id}/MPCCData_{test_id}/"
    logs = np.load(root + f"RawData_{test_id}/SimLog_{map_name}_0.npy")
    mpcc_img_path = root + f"Images_{test_id}/LocalMPCC_{map_name}_{test_id}/"
    ensure_path_exists(mpcc_img_path)

    filename = 'maps/' + map_name + "_centerline.csv"
    track = np.loadtxt(filename, delimiter=',', skiprows=1)

    # for i in range(len(logs)-100, len(logs)-50):
    # for i in range(350, 400):
    # for i in [381]:
    # for i in range(len(logs)-25, len(logs)):
    # for i in range(44, 55):
    # for i in range(1, 500):
    for i in range(1, len(logs)):
        if i % 3 != 0:
            continue
        states = np.load(mpcc_data_path + f"States_{i}.npy")
        controls = np.load(mpcc_data_path + f"Controls_{i}.npy")
        x0 = np.load(mpcc_data_path + f"States_{i}.npy")

        # fig = plt.figure(1)
        fig = plt.figure(figsize=(15, 10))
        plt.clf()
        a1 = plt.subplot2grid((4, 2), (0, 0), rowspan=3)
        ae = plt.subplot2grid((4, 2), (3, 0))
        a2 = plt.subplot2grid((4, 2), (0, 1))
        a3 = plt.subplot2grid((4, 2), (1, 1))
        a4 = plt.subplot2grid((4, 2), (2, 1))
        a5 = plt.subplot2grid((4, 2), (3, 1))

        el_lengths = np.linalg.norm(np.diff(track[:, :2], axis=0), axis=1)
        local_ss = np.insert(np.cumsum(el_lengths), 0, 0)
        psi, kappa = tph.calc_head_curv_num.calc_head_curv_num(track, el_lengths, False)
        nvecs = tph.calc_normal_vectors_ahead.calc_normal_vectors_ahead(psi)
        xs = np.interp(states[:, 3], local_ss, track[:, 0])
        ys = np.interp(states[:, 3], local_ss, track[:, 1])
        a1.plot(xs, ys, 'o', color='orange', markersize=10)

        for z in range(len(states)):
            x_line = [states[z, 0], xs[z]]
            y_line = [states[z, 1], ys[z]]
            a1.plot(x_line, y_line, '--', color='gray', linewidth=1)

        a1.plot(track[:, 0], track[:, 1], '--', linewidth=2, color='black')
        l1 = track[:, :2] + nvecs * track[:, 2][:, None]
        l2 = track[:, :2] - nvecs * track[:, 3][:, None]
        a1.plot(l1[:, 0], l1[:, 1], color='green')
        a1.plot(l2[:, 0], l2[:, 1], color='green')

        a1.plot(x0[:, 0], x0[:, 1], '-o', markersize=5, linewidth=3, color='red')

        a1.set_title(f"Action: ({logs[i+1, 7]:.3f}, {logs[i+1, 8]:.1f})")
        a1.axis('off')

        a1.set_xlim([np.min(states[:, 0]) - 2, np.max(states[:, 0]) + 2])
        a1.set_ylim([np.min(states[:, 1]) - 2, np.max(states[:, 1]) + 2])

        t_angle = np.interp(states[:, 3], local_ss, psi) + np.pi/2
        lag_errors = (-np.cos(t_angle) * (states[:, 0] - xs) - np.sin(t_angle) * (states[:, 1] - ys)) **2
        contour_errors = (np.sin(t_angle) * (states[:, 0] - xs) - np.cos(t_angle) * (states[:, 1] - ys)) **2
        total_lag = np.sum(lag_errors) * 500
        total_contour = np.sum(contour_errors) * 0.1
        print(f"{i} --> {total_lag:.2f}, {total_contour:.2f}")
        # print(np.sin(t_angle) * (states[:, 0] - xs) - np.cos(t_angle) * (states[:, 1] - ys))
        steer = np.sum(controls[:, 0] **2) * 0.001
        progress = -np.sum(controls[:, 1]) * 0.02

        ae.bar(np.arange(4), [total_lag, total_contour, steer, progress])
        ae.set_xticks(np.arange(4))
        ae.set_xticklabels(["Lag", "Contour", "Steer", "Progress"])
        # ae.set_ylim([-8, 8])
        ae.grid(True)

        vs = controls[:, 1]
        points = states[:, :2].reshape(-1, 1, 2)
        segments = np.concatenate([points[:-1], points[1:]], axis=1)

        norm = plt.Normalize(2, 8)
        lc = LineCollection(segments, cmap='jet', norm=norm)
        lc.set_array(vs)
        lc.set_linewidth(3)
        line = a1.add_collection(lc)
        plt.sca(a1)
        plt.colorbar(line)
        a1.set_aspect('equal', adjustable='box')
        a1.plot(logs[i, 0], logs[i, 1], 'x', color='red', markersize=12)


        a2.plot(controls[:, 1], label="Speed action")
        a2.plot(controls[:, 2], label="Centre line Speed")
        a2.plot([0, 2], logs[i+1, 3] * np.ones(2), '--', color='red')
        a2.set_ylabel("Speed action")
        a2.grid(True)
        # a2.set_ylim(0.8, 4.2)
        a2.set_ylim(1.5, 8.5)

        a3.plot(controls[:, 0])
        a3.set_ylabel("Steering action")
        a3.grid(True)
        # a3.set_ylim(-0.4, 0.4)

        forces = controls[:, 1] ** 2 / 0.33 * np.tan(np.abs(controls[:, 0])) * 3.71
        friction_limit = 0.6 * 9.81 * 3.71

        # print(f"Steering: {controls[:, 0]}")
        # print(f"Speeds: {controls[:, 1]}")
        # print(f"Forces: {forces}")

        a4.plot([0, 10], [friction_limit, friction_limit], '--', color='black')
        a4.plot(forces, '-o', color='red')
        a4.set_ylabel('Lateral Force')
        a4.set_ylim([0, 40])
        a4.grid(True)

        a5.plot(lag_errors, '-o', color='blue', label="Lag")
        a5.plot(contour_errors, '-o', color='red', label="Contour")
        a5.grid(True)
        a5.legend()
        a5.set_ylabel('Error')
        a5.set_ylim(0, 0.4)


        # angles_guesses = np.interp(x0[:, 3], local_ss, psi) + np.pi/2
        # a5.set_ylabel('Angle')
        # a5.plot(x0[:, 2], '-o', color='blue', label="Initial x0")
        # a5.plot(states[:, 2], '-o', color='red', label="Final solution")
        # a5.plot(angles_guesses, '-o', color='green', label="Guess")
        # a5.grid(True)
        # a5.legend()
        # # a5.set_ylim([-2, -0.5])
        # a5.set_ylim(-3.2, 3.2)
        # y_lim = -np.pi/2
        # a5.plot([0, 10], [y_lim, y_lim], '--', color='black')


        # dv = np.diff(controls[:, 1])
        # dv = np.insert(dv, 0, controls[0, 1]- logs[i+1, 3])
        # a5.plot(dv, '-o', color='red')
        # a5.set_ylabel('Acceleration')
        # a5.grid(True)

        plt.tight_layout()

        plt.savefig(mpcc_img_path + f"Raceline_{i}.svg")

        plt.close(fig)


if __name__ == '__main__':
    # render_local_maps("LocalMapPlanner", "r1")
    # render_mpcc_plans("GlobalPlanMPCC", "mu70", "esp")
    # render_mpcc_plans("GlobalPlanMPCC", "mu70", "gbr")
    # render_mpcc_plans("GlobalPlanMPCC", "max4_p0", "aut")
    # render_mpcc_plans("GlobalPlanMPCC", "max4", "aut")
    # render_mpcc_plans("FullStackMPCC", "mpcc_t3", "aut")
    # render_mpcc_plans("GlobalPlanMPCC", "max8", "aut")
    # render_mpcc_plans("GlobalPlanMPCC", "mu70", "aut")
    # render_mpcc_plans("ConstantMPCC", "mu70", "aut")
    # render_local_maps("LocalMPCC2", "r1", "aut")
    # render_local_maps("FullStackMPCC3", "m3u70", "aut")
    render_mpcc_plans("LocalMPCC", "mu60", "gbr")
