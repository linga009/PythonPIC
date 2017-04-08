"""Animates the simulation to show quantities that change over time"""
# coding=utf-8
import matplotlib.animation as anim
import matplotlib.pyplot as plt
import numpy as np

from helper_functions import colors, directions


# formatter = matplotlib.ticker.ScalarFormatter(useMathText=True, useOffset=False)


def velocity_histogram_data(arr, bins):
    """

    :param arr: particle velocity array
    :param bins: number of bins or array of edges 
    :return: x, y data on bins for linear plotting
    """
    bin_height, bin_edge = np.histogram(arr, bins=bins)
    bin_center = (bin_edge[:-1] + bin_edge[1:]) * 0.5
    return bin_center, bin_height


def animation(S, videofile_name=None, lines=False, alpha=1):
    """ animates the simulation, showing:
    * grid charge vs grid position
    * grid electric field vs grid position
    * particle phase plot (velocity vs position)
    * spatial energy modes

    S - Simulation object with run's data
    videofile_name - should be in format FILENAME.mp4;
        if not None, saves to file
    lines - boolean flag; draws particle trajectories on phase plot
    # TODO: investigate lines flag in animation
    alpha - float (0, 1) - controls opacity for phase plot

    returns: matplotlib figure with animation
    """
    fig = plt.figure(figsize=(10, 8))
    grid_axes = [fig.add_subplot(321 + 2 * i) for i in range(3)]
    distribution_axes = fig.add_subplot(322)
    # TODO: add magnetic field
    phase_axes = fig.add_subplot(324)
    freq_axes = fig.add_subplot(326)

    iteration = freq_axes.text(0.1, 0.9, 'i=x', horizontalalignment='left',
                               verticalalignment='center', transform=freq_axes.transAxes)

    fig.suptitle(str(S), fontsize=12)
    fig.subplots_adjust(top=0.81, bottom=0.08, left=0.15, right=0.95,
                        wspace=.25, hspace=0.3)  # TODO: remove particle windows if there are no particles

    charge_plots = []
    current_plots = []
    for i, species in enumerate(S.list_species):
        charge_plots.append(
            grid_axes[0].plot(S.grid.x, S.grid.charge_density_history[0, :, i], ".-", color=colors[i], alpha=0.1)[0])
        for j in range(3):
            current_plots.append(grid_axes[j].plot(S.grid.x, S.grid.current_density_history[0, :, j, i], ".-",
                                                   color=colors[3 * i + j], alpha=0.9,
                                                   label=f"{species.name} $j_{directions[j]}$")[0])
    for j in range(3):
        grid_axes[j].set_xlim(0, S.grid.L)
        grid_axes[j].set_ylabel(f"Current density $j_{directions[j]}$", color='b')
        grid_axes[j].tick_params('y', colors='b')
        grid_axes[j].set_xlabel(r"Position $x$")
        grid_axes[j].ticklabel_format(style='sci', axis='both', scilimits=(0, 0), useMathText=True, useOffset=False)
        mincharge = np.min(S.grid.current_density_history)
        maxcharge = np.max(S.grid.current_density_history)
        grid_axes[j].set_ylim(mincharge, maxcharge)
        grid_axes[j].grid()
        grid_axes[j].legend(loc='lower left')

    field_axes = grid_axes[0].twinx()
    field_axes.set_xlim(0, S.grid.L)
    field_plot, = field_axes.plot([], [], "r.-", label="$E_x$")
    field_axes.set_ylabel(r"Electric field $E$", color='r')
    field_axes.tick_params('y', colors='r')
    field_axes.ticklabel_format(style='sci', axis='both', scilimits=(0, 0), useMathText=True, useOffset=False)
    maxfield = np.max(np.abs(S.grid.electric_field_history))
    field_axes.grid()
    field_axes.legend()
    field_axes.set_ylim(-maxfield, maxfield)

    phase_dots = {}
    phase_lines = {}
    for i, species in enumerate(S.list_species):
        phase_dots[species.name], = phase_axes.plot([], [], colors[i] + ".", alpha=alpha)
        if lines:
            phase_lines[species.name], = phase_axes.plot([], [], colors[i] + "-", alpha=alpha / 2, lw=0.7)
    try:
        maxv = max([10 * np.mean(np.abs(species.velocity_history)) for species in S.list_species])
        phase_axes.set_ylim(-maxv, maxv)
    except ValueError:
        pass
    phase_axes.set_xlim(0, S.grid.L)
    phase_axes.set_xlabel(r"Particle position $x$")
    phase_axes.set_ylabel(r"Particle velocity $v_x$")
    phase_axes.ticklabel_format(style='sci', axis='both', scilimits=(0, 0), useMathText=True, useOffset=False)
    phase_axes.grid()

    histograms = []
    bin_arrays = []
    for i, s in enumerate(S.list_species):
        bin_array = np.linspace(s.velocity_history.min(), s.velocity_history.max())
        bin_arrays.append(bin_array)
        histograms.append(
            distribution_axes.plot(*velocity_histogram_data(s.velocity_history[0], bin_array), colors[i])[0])
    distribution_axes.grid()
    distribution_axes.yaxis.tick_right()
    distribution_axes.yaxis.set_label_position("right")
    distribution_axes.set_xlabel(r"Velocity $v$")
    distribution_axes.set_ylabel(r"Number of particles")
    distribution_axes.ticklabel_format(style='sci', axis='both', scilimits=(0, 0), useMathText=True, useOffset=False)

    freq_plot, = freq_axes.plot([], [], "bo-", label="energy per mode")
    freq_axes.set_xlabel(r"Wavevector mode $k$")
    freq_axes.set_ylabel(r"Energy $E$")
    freq_axes.set_xlim(0, S.grid.NG / 2)
    freq_axes.set_ylim(S.grid.energy_per_mode_history.min(), S.grid.energy_per_mode_history.max())
    freq_axes.grid()
    freq_axes.ticklabel_format(style='sci', axis='y', scilimits=(0, 0), useMathText=True, useOffset=False)
    freq_axes.yaxis.tick_right()
    freq_axes.yaxis.set_label_position("right")

    def init():
        """initializes animation window for faster drawing"""
        iteration.set_text("Iteration: ")
        field_plot.set_data(S.grid.x, np.zeros_like(S.grid.x))
        freq_plot.set_data(S.grid.k_plot, np.zeros_like(S.grid.k_plot))
        for i, species, histogram in zip(range(S.grid.n_species), S.list_species, histograms):
            charge_plots[i].set_data(S.grid.x, np.zeros_like(S.grid.x))
            phase_dots[species.name].set_data([], [])
            for j in range(3):
                current_plots[3 * i + j].set_data(S.grid.x, np.zeros_like(S.grid.x))
            if lines:
                phase_lines[species.name].set_data([], [])
            histogram.set_data([], [])
        if lines:
            return [*current_plots, *charge_plots, field_plot, *phase_dots.values(), iteration,
                    *phase_lines.values()]
        else:
            return [*current_plots, *charge_plots, field_plot, freq_plot, *phase_dots.values(), iteration]

    def animate(i):
        """draws the i-th frame of the simulation"""
        field_plot.set_ydata(S.grid.electric_field_history[i])
        freq_plot.set_ydata(S.grid.energy_per_mode_history[i])
        for i_species, species, histogram, bin_array in zip(range(S.grid.n_species), S.list_species, histograms,
                                                            bin_arrays):
            charge_plots[i_species].set_ydata(S.grid.charge_density_history[i, :, i_species])
            phase_dots[species.name].set_data(species.position_history[i, :], species.velocity_history[i, :, 0])
            for j in range(3):
                current_plots[3 * i_species + j].set_ydata(S.grid.current_density_history[i, :, j, i_species])
            if lines:
                phase_lines[species.name].set_data(species.position_history[:i + 1, ::10].T,
                                                   species.velocity_history[:i + 1, ::10, 0].T)
            histogram.set_data(*velocity_histogram_data(species.velocity_history[i], bin_array))
        iteration.set_text(f"Iteration: {i}/{S.NT}\nTime: {i*S.dt:.3g}/{S.NT*S.dt:.3g}")

        if lines:
            return [*current_plots, *charge_plots, field_plot, freq_plot, *histograms, *phase_dots.values(),
                    iteration,
                    *phase_lines.values()]
        else:
            return [*current_plots, *charge_plots, field_plot, freq_plot, *histograms, *phase_dots.values(),
                    iteration]

    animation_object = anim.FuncAnimation(fig, animate, interval=100, frames=np.arange(0, S.NT, int(np.log10(S.NT))),
                                          blit=True, init_func=init)
    if videofile_name:
        print(f"Saving animation to {videofile_name}")
        animation_object.save(videofile_name, fps=15, writer='ffmpeg', extra_args=['-vcodec', 'libx264'])
        print(f"Saved animation to {videofile_name}")
    return animation_object


if __name__ == "__main__":
    import Simulation

    S = Simulation.load_data("data_analysis/TS2/TS2.hdf5")
    anim = animation(S, "")
    plt.show()
