
import React from 'react';
import { Link } from 'react-router-dom';
import { ICONS } from '../constants';

export interface Crumb {
    label: string;
    href: string;
    icon?: React.ReactElement;
}

interface BreadcrumbsProps {
    crumbs: Crumb[];
}

const Breadcrumbs: React.FC<BreadcrumbsProps> = ({ crumbs }) => {
    return (
        <nav aria-label="Breadcrumb" className="flex items-center text-sm text-gray-400 mb-6">
            {crumbs.map((crumb, index) => {
                const isLast = index === crumbs.length - 1;
                return (
                    <React.Fragment key={index}>
                        {index > 0 && (
                             <span className="mx-2 text-gray-500">/</span>
                        )}
                        {isLast ? (
                            <span className="font-semibold text-white flex items-center gap-1.5">
                                {crumb.icon && React.cloneElement(crumb.icon, { ...crumb.icon.props, className: "h-4 w-4" })}
                                {crumb.label}
                            </span>
                        ) : (
                            <Link to={crumb.href} className="hover:text-white hover:underline flex items-center gap-1.5">
                               {crumb.icon && React.cloneElement(crumb.icon, { ...crumb.icon.props, className: "h-4 w-4" })}
                               {crumb.label}
                            </Link>
                        )}
                    </React.Fragment>
                );
            })}
        </nav>
    );
};

export default Breadcrumbs;
