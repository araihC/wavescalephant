import argparse
from scipy.ndimage.filters import convolve as conv
from scipy.ndimage import gaussian_filter
<<<<<<< HEAD:pipeline/stage04_wavefront_detection/scripts/horn_schunck.py
=======
from scipy.signal import hilbert
import time
>>>>>>> 1b82ec0e43e45e9e4b9a01ffcef7fb650cf0d575:pipeline/stage04_wave_detection/scripts/horn_schunck.py
import neo
import numpy as np
from copy import copy
import matplotlib.pyplot as plt
from utils import load_neo, write_neo, none_or_str, save_plot, \
                  ImageSequence2AnalogSignal, AnalogSignal2ImageSequence

# ToDo: enable phase velocity fields
# xydiff = np.mod(x - y + np.pi, 2*np.pi) - np.pi

def get_derviation_kernels(name='Simple'):
    if name=='Simple' or name is None:
        kernelX = np.array([[-1, 1],
                            [-1, 1]], dtype=np.float) * .25
        kernelY = np.array([[-1, -1],
                            [ 1,  1]], dtype=np.float) * .25
    elif name=='Prewitt':
        kernelX = np.array([[-1, 0, 1],
                            [-1, 0, 1],
                            [-1, 0, 1]], dtype=np.float) * 1/6
        kernelY = np.array([[-1, -1, -1],
                            [ 0,  0,  0],
                            [ 1,  1,  1]], dtype=np.float) * 1/6
    elif name=='Sobel':
        kernelX = np.array([[-1, 0, 1],
                            [-2, 0, 2],
                            [-1, 0, 1]], dtype=np.float) * 1/8
        kernelY = np.array([[-1, -2, -1],
                            [ 0,  0,  0],
                            [ 1,  2,  1]], dtype=np.float) * 1/8
    elif name=='Roberts':
        kernelX = np.array([[ 0, 1],
                            [-1, 0]], dtype=np.float) * 0.5
        kernelY = np.array([[-1, 0],
                            [ 0, 1]], dtype=np.float) * 0.5
    else:
        print('Deriviative name {name} is not implemented, '\
            + 'using simple filter instead. \n Available filters: "Simple", '\
            + '"Prewitt", "Sobel", "Roberts".')
        return get_derviation_kernels()

    return kernelX, kernelY


def horn_schunck_step(frame, next_frame, alpha, max_Niter, convergence_limit,
                      kernelHS, kernelT, kernelX, kernelY):
    """
    Parameters
    ----------
    frame: numpy.ndarray
        image at t=0
    next_frame: numpy.ndarray
        image at t=1
    alpha: float
        regularization constant
    max_Niter: int
        maximum number of iteration
    convergence_limit: float
        the maximum absolute change between iterations defining convergence
    """
    # set up initial velocities
    vx = np.zeros_like(frame)
    vy = np.zeros_like(frame)

    # Estimate derivatives
    [fx, fy, ft] = compute_derivatives(frame, next_frame,
                                       kernelX=kernelX,
                                       kernelY=kernelY,
                                       kernelT=kernelT)
    # Iteration to reduce error
    for i in range(max_Niter):
        # Compute local averages of the flow vectors (smoothness constraint)
        vx_avg = conv(vx, kernelHS)
        vy_avg = conv(vy, kernelHS)
        # common part of update step (brightness constancy)
        der = (fx*vx_avg + fy*vy_avg + ft) / (alpha**2 + fx**2 + fy**2)
        # iterative step
        new_vx = vx_avg - fx * der
        new_vy = vy_avg - fy * der
        # check convergence
        max_dv = np.max([np.max(np.abs(vx-new_vx)),
                         np.max(np.abs(vy-new_vy))])
        vx, vy = new_vx, new_vy
        if max_dv < convergence_limit:
            break
    return vx + vy*1j


<<<<<<< HEAD:pipeline/stage04_wavefront_detection/scripts/horn_schunck.py
def compute_derivatives(frame, next_frame, kernelX, kernelY, kernelT):
    fx = conv(frame, kernelX) + conv(next_frame, kernelX)
    fy = conv(frame, kernelY) + conv(next_frame, kernelY)
    ft = conv(frame, kernelT) + conv(next_frame, -kernelT)
=======
norm_angle = lambda p: -np.mod(p + np.pi, 2*np.pi) + np.pi

def phase_conv2D(frame, kernel, kernel_center):
    dx, dy = kernel.shape
    dimx, dimy = frame.shape
    dframe = np.zeros_like(frame)
    # inverse kernel to mimic behavior or regular convolution algorithm
    k = kernel[::-1, ::-1]
    ci = dx - 1 - kernel_center[0]
    cj = dy - 1 - kernel_center[1]
    # loop over kernel window for each frame site
    for i,j in zip(*np.where(np.isfinite(frame))):
        phase = frame[i,j]
        dphase = np.zeros((dx,dy), dtype=float)
        for di,dj in itertools.product(range(dx), range(dy)):
            # kernelsite != 0, framesite within borders and != nan
            if k[di,dj] and i+di-ci < dimx and j+dj-cj < dimy \
            and np.isfinite(frame[i+di-ci,j+dj-cj]):
                sign = -1*np.sign(k[di,dj])
                # pos = clockwise from phase to frame[..]
                dphase[di,dj] = sign*norm_angle(phase-frame[i+di-ci,j+dj-cj])
        if dphase.any():
            dframe[i,j] = np.average(dphase, weights=abs(k)) / np.pi
    return dframe


def compute_derivatives(frame, next_frame, kernelX, kernelY, kernelT,
                        are_phases=False, kernel_center=None):
    if are_phases:
        fx = phase_conv2D(frame, kernelX, kernel_center) \
           + phase_conv2D(next_frame, kernelX, kernel_center)
        fy = phase_conv2D(frame, kernelY, kernel_center) \
           + phase_conv2D(next_frame, kernelY, kernel_center)
        ft = norm_angle(frame - next_frame)
    else:
        fx = conv(frame, kernelX) + conv(next_frame, kernelX)
        fy = conv(frame, kernelY) + conv(next_frame, kernelY)
        # ft = conv(frame, kernelT) + conv(next_frame, -kernelT)
        ft = frame - next_frame
>>>>>>> 1b82ec0e43e45e9e4b9a01ffcef7fb650cf0d575:pipeline/stage04_wave_detection/scripts/horn_schunck.py
    return fx, fy, ft


def horn_schunck(frames, alpha, max_Niter, convergence_limit,
<<<<<<< HEAD:pipeline/stage04_wavefront_detection/scripts/horn_schunck.py
                 kernelHS, kernelT, kernelX, kernelY):
    nan_channels = np.where(np.bitwise_not(np.isfinite(frames[0])))
    frames[:,nan_channels[0],nan_channels[1]] = np.nanmedian(frames)
=======
                 kernelHS, kernelT, kernelX, kernelY,
                 are_phases=False, kernel_center=None):

    nan_channels = np.where(np.bitwise_not(np.isfinite(frames[0])))
    frames = interpolate_empty_sites(frames, are_phases)
>>>>>>> 1b82ec0e43e45e9e4b9a01ffcef7fb650cf0d575:pipeline/stage04_wave_detection/scripts/horn_schunck.py

    vector_frames = np.zeros(frames.shape, dtype=complex)

    for i, frame in enumerate(frames[:-1]):
        next_frame = frames[i+1]

        vector_frames[i] = horn_schunck_step(frame,
                                             next_frame,
                                             alpha=alpha,
                                             max_Niter=max_Niter,
                                             convergence_limit=convergence_limit,
                                             kernelHS=kernelHS,
                                             kernelT=kernelT,
                                             kernelX=kernelX,
                                             kernelY=kernelY)
        vector_frames[i][nan_channels] = np.nan + np.nan*1j

    frames[:,nan_channels[0],nan_channels[1]] = np.nan
    return vector_frames


def interpolate_empty_sites(frames, are_phases=False):
    if np.isfinite(frames).all():
        return frames
    dim_x, dim_y = frames[0].shape
    grid = np.meshgrid([-1,0,1],[-1,0,1])

    for i, frame in enumerate(frames):
        new_frame = copy(frame)
        while not np.isfinite(new_frame).all():
            x, y = np.where(np.bitwise_not(np.isfinite(new_frame)))
            # loop over nan-sites
            for xi, yi in zip(x,y):
                neighbours = []
                # collect neighbours of each site
                for dx, dy in zip(grid[0].flatten(), grid[1].flatten()):
                    xn = xi+dx
                    yn = yi+dy
                    if (0 <= xn) & (xn < dim_x) & (0 <= yn) & (yn < dim_y):
                        neighbours.append(frames[i, xn, yn])
                # average over neihbour values
                if np.isfinite(neighbours).any():
                    if are_phases:
                        vectors = np.exp(1j*np.array(neighbours))
                        new_frame[xi,yi] = np.angle(np.nansum(vectors))
                    else:
                        new_frame[xi,yi] = np.nansum(neighbours)
            frames[i] = new_frame
    return frames


def smooth_frames(frames, sigma):
    # replace nan sites by median
    if np.isfinite(frames).any():
        # assume constant nan sites over time
        nan_sites = np.where(np.bitwise_not(np.isfinite(frames[0])))
        if np.iscomplexobj(frames):
            frames[:,nan_sites[0],nan_sites[1]] = np.nanmedian(np.real(frames)) \
                                                + np.nanmedian(np.imag(frames))*1j
        else:
            frames[:,nan_sites[0],nan_sites[1]] = np.nanmedian(frames)
    else:
        nan_sites = None

    # apply gaussian filter
    if np.iscomplexobj(frames):
        frames = gaussian_filter(np.real(frames), sigma=sigma, mode='nearest') \
               + gaussian_filter(np.imag(frames), sigma=sigma, mode='nearest')*1j
    else:
        frames = gaussian_filter(frames, sigma=sigma, mode='nearest')

    # set nan sites back to nan
    if nan_sites is not None:
        if np.iscomplexobj(frames):
            frames[:,nan_sites[0],nan_sites[1]] = np.nan + np.nan*1j
        else:
            frames[:,nan_sites[0],nan_sites[1]] = np.nan

    return frames


def plot_opticalflow(frame, vec_frame, skip_step=None):
    # Every <skip_step> point in each direction.
    fig, ax = plt.subplots()
    dim_x, dim_y = vec_frame.shape
    img = ax.imshow(frame, interpolation='nearest',
                    cmap=plt.get_cmap('viridis'))
    plt.colorbar(img, ax=ax)
    if skip_step is None:
        skip_step = int(min([dim_x, dim_y]) / 50) + 1

    ax.quiver(np.arange(dim_y)[::skip_step],
              np.arange(dim_x)[::skip_step],
              np.real(vec_frame[::skip_step,::skip_step]),
              -np.imag(vec_frame[::skip_step,::skip_step]))

    ax.axis('image')
    ax.set_xticks([])
    ax.set_yticks([])
    return ax


if __name__ == '__main__':
    CLI = argparse.ArgumentParser(description=__doc__,
                   formatter_class=argparse.RawDescriptionHelpFormatter)
    CLI.add_argument("--data", nargs='?', type=str, required=True,
                     help="path to input data in neo format")
    CLI.add_argument("--output", nargs='?', type=str, required=True,
                     help="path of output file")
    CLI.add_argument("--output_img", nargs='?', type=none_or_str, default=None,
                     help="path of output image file")
    CLI.add_argument("--alpha", nargs='?', type=float, default=0.001,
                     help='regularization parameter')
    CLI.add_argument("--max_Niter", nargs='?', type=int, default=50,
                     help='maximum number of iterations')
    CLI.add_argument("--convergence_limit", nargs='?', type=float, default=10e-3,
                     help='absolute change at which consider optimization converged')
    CLI.add_argument("--gaussian_sigma", nargs='+', type=float, default=[0,3,3],
                     help='sigma of gaussian filter in each dimension')
    CLI.add_argument("--derivative_filter", nargs='?', type=str, default='Simple',
                     help='Filter kernel to use for calculating spatial derivatives')

    args = CLI.parse_args()
    block = load_neo(args.data)

    block = AnalogSignal2ImageSequence(block)
    imgseq = block.segments[0].imagesequences[-1]
    asig = block.segments[0].analogsignals[-1]

    frames = imgseq.as_array()
    # frames /= np.nanmax(np.abs(frames))

    kernelHS = np.array([[1, 2, 1],
                         [2, 0, 2],
                         [1, 2, 1]], dtype=np.float) * 1/12
    kernelT = np.ones((2, 2), dtype=np.float) * .25
    kernelX, kernelY = get_derviation_kernels(args.derivative_filter)

    vector_frames = horn_schunck(frames=frames,
                                 alpha=args.alpha,
                                 max_Niter=args.max_Niter,
                                 convergence_limit=args.convergence_limit,
                                 kernelX=kernelX,
                                 kernelY=kernelY,
                                 kernelT=kernelT,
                                 kernelHS=kernelHS)

    if np.sum(args.gaussian_sigma):
        vector_frames = smooth_frames(vector_frames, sigma=args.gaussian_sigma)

    vec_imgseq = neo.ImageSequence(vector_frames,
                                   units='dimensionless',
                                   dtype=complex,
                                   # t_start=imgseq.t_start,
                                   spatial_scale=imgseq.spatial_scale,
                                   sampling_rate=imgseq.sampling_rate,
                                   name='Optical Flow',
                                   description='Horn-Schunck estimation of optical flow',
                                   file_origin=imgseq.file_origin,
                                   **imgseq.annotations)

    if args.output_img is not None:
        ax = plot_opticalflow(frames[0], vector_frames[0], skip_step=3)
        ax.set_ylabel(f'pixel size: {imgseq.spatial_scale} '\
                    + imgseq.spatial_scale.units.dimensionality.string)
        ax.set_xlabel('{:.3f} s'.format(asig.times[0].rescale('s')))
        save_plot(args.output_img)

    block.segments[0].imagesequences = [vec_imgseq]
    block = ImageSequence2AnalogSignal(block)
    write_neo(args.output, block)
