import React from 'react';
import './SkeletonLoader.css';

const SkeletonLoader = ({ type = 'text', count = 1, height, width, className = '' }) => {
    const skeletons = Array.from({ length: count });

    const getStyles = () => {
        const styles = {};
        if (height) styles.height = height;
        if (width) styles.width = width;
        return styles;
    };

    // Render different skeleton types
    const renderSkeleton = (index) => {
        switch (type) {
            case 'card':
                return (
                    <div key={index} className="skeleton-card shimmer" style={getStyles()}>
                        <div className="skeleton-card-header"></div>
                        <div className="skeleton-card-body">
                            <div className="skeleton-line"></div>
                            <div className="skeleton-line short"></div>
                        </div>
                    </div>
                );
            case 'table':
                return (
                    <div key={index} className="skeleton-table shimmer">
                        <div className="skeleton-table-header"></div>
                        <div className="skeleton-table-row"></div>
                        <div className="skeleton-table-row"></div>
                        <div className="skeleton-table-row"></div>
                    </div>
                );
            case 'chart':
                return (
                    <div key={index} className="skeleton-chart shimmer" style={getStyles()}>
                        <div className="skeleton-chart-bars">
                            <div className="skeleton-bar" style={{ height: '60%' }}></div>
                            <div className="skeleton-bar" style={{ height: '80%' }}></div>
                            <div className="skeleton-bar" style={{ height: '40%' }}></div>
                            <div className="skeleton-bar" style={{ height: '90%' }}></div>
                        </div>
                    </div>
                );
            default:
                return (
                    <div
                        key={index}
                        className={`skeleton-item skeleton-${type} shimmer`}
                        style={getStyles()}
                    />
                );
        }
    };

    return (
        <div className={`skeleton-container ${className}`}>
            {skeletons.map((_, index) => renderSkeleton(index))}
        </div>
    );
};

export default SkeletonLoader;
